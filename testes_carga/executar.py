"""
Executa a bateria de testes de carga para Python e Node.js e salva os resultados.

Para cada repetição e cada combinação (linguagem, tecnologia) em ordem embaralhada:
  1. sobe um servidor novo (dados iniciais limpos);
  2. faz um aquecimento rápido;
  3. roda o k6 para cada carga de trabalho e cada nível de concorrência;
  4. desliga o servidor.

Isolamento de CPU (máquina com núcleos P e E):
  - servidor -> CPUs 0-3 (núcleos de desempenho)
  - k6       -> CPUs 4-11 (núcleos de eficiência)

Uso:
  uv run python -m testes_carga.executar --enxuto     # 2 reps × 3s (~12 min, 2 linguagens)
  uv run python -m testes_carga.executar              # 3 reps × 20s (~110 min, 2 linguagens)
  uv run python -m testes_carga.executar --rapido     # 1 rep × 2s (~5 min, conferência)

Por segurança, cada execução grava em uma nova pasta dentro de
resultados/execucoes/ (a menos que --saida seja informado).
"""

import argparse
import csv
import json
import os
import platform
import random
import statistics
import subprocess
import time
from datetime import datetime
from pathlib import Path

from python_api.comum import servidores

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parent
K6 = RAIZ / "ferramentas" / "k6"
RESULTADOS = RAIZ / "resultados"

CPUS_SERVIDOR = [0, 1, 2, 3]
CPUS_K6 = "4-11"

LINGUAGENS = ["python", "node"]
TECNOLOGIAS = ["rest", "graphql", "grpc", "soap"]
CARGAS = ["leve", "pesada", "escrita"]
NIVEIS_VUS = [1, 10, 50, 100]


def nome_servidor(linguagem, tecnologia):
    return tecnologia if linguagem == "python" else f"{tecnologia}_node"


def rodar_k6(linguagem, tecnologia, carga, vus, duracao, saida):
    comando = ["taskset", "-c", CPUS_K6, str(K6), "run", "--quiet",
               "-e", f"LINGUAGEM={linguagem}", "-e", f"TECNOLOGIA={tecnologia}",
               "-e", f"CARGA={carga}", "-e", f"VUS={vus}",
               "-e", f"DURACAO={duracao}", "-e", f"SAIDA={saida}", "carga.js"]
    resultado = subprocess.run(comando, cwd=PASTA, capture_output=True, text=True)
    if resultado.returncode != 0 or not Path(saida).exists():
        raise RuntimeError(
            f"k6 falhou ({linguagem}/{tecnologia}/{carga}/{vus}):\n{resultado.stderr[-2000:]}"
        )
    return json.loads(Path(saida).read_text())


def registrar_ambiente(args, linguagens, tecnologias, destino):
    def comando(*c):
        try:
            return subprocess.run(c, capture_output=True, text=True).stdout.strip()
        except OSError:
            return "?"
    modelo = next((linha.split(":", 1)[1].strip() for linha in
                   Path("/proc/cpuinfo").read_text().splitlines()
                   if linha.startswith("model name")), "?")
    ambiente = {
        "inicio": datetime.now().isoformat(timespec="seconds"),
        "cpu": modelo,
        "nucleos": os.cpu_count(),
        "memoria": comando("free", "-h").splitlines()[1] if comando("free", "-h") else "?",
        "sistema": platform.platform(),
        "python": platform.python_version(),
        "node": comando("node", "--version"),
        "k6": comando(str(K6), "version"),
        "carga_media_antes (1/5/15 min)": os.getloadavg(),
        "cpus_servidor": CPUS_SERVIDOR,
        "cpus_k6": CPUS_K6,
        "repeticoes": args.repeticoes,
        "duracao_por_teste": args.duracao,
        "linguagens": linguagens,
        "tecnologias": tecnologias,
        "niveis_vus": args.vus,
        "cargas": args.cargas,
    }
    (destino / "ambiente.json").write_text(json.dumps(ambiente, indent=2, ensure_ascii=False))


def consolidar(brutos, destino):
    """Junta as repetições: mediana de cada métrica, mínimo e máximo da vazão."""
    grupos = {}
    for r in brutos:
        chave = (r.get("linguagem", "python"), r["tecnologia"], r["carga"], r["vus"])
        grupos.setdefault(chave, []).append(r)

    linhas = []
    for (ling, tec, carga, vus), rs in sorted(grupos.items()):
        med = lambda campo: statistics.median(r[campo] for r in rs)
        linhas.append({
            "linguagem": ling, "tecnologia": tec, "carga": carga, "vus": vus,
            "repeticoes": len(rs),
            "req_por_s": round(med("requisicoes_por_s"), 1),
            "req_por_s_min": round(min(r["requisicoes_por_s"] for r in rs), 1),
            "req_por_s_max": round(max(r["requisicoes_por_s"] for r in rs), 1),
            "latencia_media_ms": round(med("latencia_media_ms"), 3),
            "latencia_mediana_ms": round(med("latencia_mediana_ms"), 3),
            "latencia_p95_ms": round(med("latencia_p95_ms"), 3),
            "latencia_p99_ms": round(med("latencia_p99_ms"), 3),
            "taxa_erros": max(r["taxa_erros"] for r in rs),
            "bytes_recebidos_por_req": round(med("bytes_recebidos_por_req")),
            "bytes_enviados_por_req": round(med("bytes_enviados_por_req")),
        })

    with open(destino / "resultados.csv", "w", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)
    return linhas


def _validar_lista(itens, permitidos, nome):
    if not itens:
        raise ValueError(f"--{nome} não pode ser vazio")
    if len(set(itens)) != len(itens):
        raise ValueError(f"--{nome} contém valores repetidos: {itens}")
    invalidos = [x for x in itens if x not in permitidos]
    if invalidos:
        raise ValueError(f"--{nome} inválido: {invalidos} (permitidos: {permitidos})")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repeticoes", type=int, default=3)
    parser.add_argument("--duracao", default="20s", help="duração de cada teste (k6)")
    parser.add_argument("--pausa", type=float, default=2.0, help="pausa entre testes em s")
    parser.add_argument("--aquecimento", default="3s", help="duração do aquecimento")
    parser.add_argument("--vus", default=",".join(map(str, NIVEIS_VUS)))
    parser.add_argument("--cargas", default=",".join(CARGAS))
    parser.add_argument("--tecnologias", default=",".join(TECNOLOGIAS))
    parser.add_argument("--linguagens", default=",".join(LINGUAGENS))
    parser.add_argument("--enxuto", action="store_true",
                        help="2 repetições de 3s, pausa 0.5s (~12 min para as 2 linguagens)")
    parser.add_argument("--rapido", action="store_true",
                        help="1 repetição de 2s, pausa 0.5s (~5 min, conferência)")
    parser.add_argument("--saida", type=Path, default=None,
                        help="pasta de saída (padrão: nova pasta em resultados/execucoes/)")
    args = parser.parse_args()
    if args.enxuto:
        args.repeticoes, args.duracao, args.pausa, args.aquecimento = 2, "3s", 0.5, "1s"
    elif args.rapido:
        args.repeticoes, args.duracao, args.pausa, args.aquecimento = 1, "2s", 0.5, "1s"

    if args.repeticoes <= 0:
        parser.error("--repeticoes deve ser maior que zero")
    try:
        args.vus = [int(v) for v in args.vus.split(",") if v.strip()]
    except ValueError:
        parser.error("--vus deve conter apenas inteiros separados por vírgula")
    if not args.vus or any(v <= 0 for v in args.vus) or len(set(args.vus)) != len(args.vus):
        parser.error("--vus deve conter inteiros positivos e sem repetição")

    args.cargas = [c.strip() for c in args.cargas.split(",") if c.strip()]
    tecnologias = [t.strip() for t in args.tecnologias.split(",") if t.strip()]
    linguagens = [l.strip() for l in args.linguagens.split(",") if l.strip()]
    try:
        _validar_lista(args.cargas, CARGAS, "cargas")
        _validar_lista(tecnologias, TECNOLOGIAS, "tecnologias")
        _validar_lista(linguagens, LINGUAGENS, "linguagens")
    except ValueError as erro:
        parser.error(str(erro))

    if args.saida is not None:
        destino = args.saida.resolve()
    else:
        etiqueta = "enxuto" if args.enxuto else ("rapido" if args.rapido else "execucao")
        carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
        destino = (RESULTADOS / "execucoes" / f"{carimbo}_{etiqueta}").resolve()

    pasta_brutos = destino / "bruto"
    pasta_brutos.mkdir(parents=True, exist_ok=True)
    registrar_ambiente(args, linguagens, tecnologias, destino)
    print(f"Salvando esta execução em {destino}", flush=True)

    pares = [(ling, tec) for ling in linguagens for tec in tecnologias]
    total = args.repeticoes * len(pares) * len(args.cargas) * len(args.vus)
    feitos, brutos, inicio = 0, [], time.time()
    aquecimento_arquivo = destino / "aquecimento_k6.json"

    for rep in range(1, args.repeticoes + 1):
        ordem = pares[:]
        random.Random(rep).shuffle(ordem)
        for ling, tec in ordem:
            srv_nome = nome_servidor(ling, tec)
            with open(destino / f"servidor_{ling}_{tec}.log", "a") as log:
                servidor = servidores.iniciar(srv_nome, cpus=CPUS_SERVIDOR, saida=log)
                try:
                    for carga in args.cargas:
                        rodar_k6(ling, tec, carga, 10, args.aquecimento, aquecimento_arquivo)
                    for carga in args.cargas:
                        for vus in args.vus:
                            saida = pasta_brutos / f"r{rep}_{ling}_{tec}_{carga}_{vus}.json"
                            r = rodar_k6(ling, tec, carga, vus, args.duracao, saida)
                            r["repeticao"] = rep
                            brutos.append(r)
                            feitos += 1
                            print(f"[{feitos:3}/{total}] rep {rep} {ling:6} {tec:7} {carga:7} "
                                  f"{vus:3} VUs -> {r['requisicoes_por_s']:8.1f} req/s  "
                                  f"p95 {r['latencia_p95_ms']:8.2f} ms  "
                                  f"erros {r['taxa_erros']:.2%}  "
                                  f"({(time.time() - inicio) / 60:.1f} min)", flush=True)
                            time.sleep(args.pausa)
                finally:
                    servidores.parar(servidor)
            time.sleep(1.0)

    consolidar(brutos, destino)
    print(f"\nPronto! Resultados em {destino}/resultados.csv")


if __name__ == "__main__":
    main()
