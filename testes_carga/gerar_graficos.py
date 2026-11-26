"""
Gera os gráficos dos testes de carga a partir de resultados/resultados.csv.
Suporta tanto CSV com 1 linguagem (Python) quanto com 2 linguagens (Python + Node.js),
gerando gráficos por linguagem e um comparativo direto Python × Node.js.

Uso:  uv run python -m testes_carga.gerar_graficos [--csv caminho/resultados.csv]
"""

import argparse
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent

ESTILO = {
    "rest":    {"nome": "REST",    "cor": "#2a78d6", "marcador": "o"},
    "graphql": {"nome": "GraphQL", "cor": "#eb6834", "marcador": "s"},
    "grpc":    {"nome": "gRPC",    "cor": "#1baf7a", "marcador": "^"},
    "soap":    {"nome": "SOAP",    "cor": "#eda100", "marcador": "D"},
}
ORDEM = ["rest", "graphql", "grpc", "soap"]
NOME_LING = {"python": "Python", "node": "Node.js"}

TITULO_CARGA = {
    "leve": "Carga leve (consultas pequenas)",
    "pesada": "Carga pesada (listar todas as 1000 músicas)",
    "escrita": "Carga de escrita (criar, alterar e remover usuário)",
}

TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"
GRADE = "#e4e3df"
FUNDO = "#ffffff"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 13,
    "axes.edgecolor": GRADE,
    "axes.labelcolor": TEXTO_2,
    "axes.titlecolor": TEXTO,
    "xtick.color": TEXTO_2,
    "ytick.color": TEXTO_2,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": FUNDO,
    "axes.facecolor": FUNDO,
})


def ler(caminho):
    with open(caminho) as arquivo:
        linhas = list(csv.DictReader(arquivo))
    for linha in linhas:
        linha.setdefault("linguagem", "python")
        for campo, valor in linha.items():
            if campo not in ("linguagem", "tecnologia", "carga"):
                linha[campo] = float(valor)
    return linhas


def milhar(valor, _=None):
    return f"{valor:,.0f}".replace(",", ".")


def rotular_fim_das_linhas(ax, finais, formato):
    finais = sorted(finais, key=lambda f: f[1])
    y_min, y_max = ax.get_ylim()
    log = ax.get_yscale() == "log"
    transf = (lambda v: math.log10(v)) if log else (lambda v: v)
    inv = (lambda v: 10 ** v) if log else (lambda v: v)
    espaco = (transf(y_max) - transf(y_min)) * 0.07
    posicoes = []
    for x, y, tec in finais:
        pos = transf(y)
        if posicoes and pos - posicoes[-1] < espaco:
            pos = posicoes[-1] + espaco
        posicoes.append(pos)
        ax.annotate(f"{ESTILO[tec]['nome']}  {formato(y)}", xy=(x, y),
                    xytext=(x, inv(pos)), textcoords="data",
                    xycoords="data", ha="left", va="center", fontsize=12,
                    color=TEXTO, fontweight="bold",
                    annotation_clip=False)


def grafico_linhas(linhas, carga, metrica, titulo_y, arquivo, sufixo_titulo="", log=False, faixa=None):
    dados = [l for l in linhas if l["carga"] == carga]
    if not dados:
        return
    niveis = sorted({int(l["vus"]) for l in dados})
    posicoes = list(range(len(niveis)))

    fig, ax = plt.subplots(figsize=(12, 6.2), dpi=150)
    finais = []
    for tec in ORDEM:
        serie = sorted((l for l in dados if l["tecnologia"] == tec), key=lambda l: l["vus"])
        if not serie:
            continue
        xs = [niveis.index(int(l["vus"])) for l in serie]
        ys = [l[metrica] for l in serie]
        estilo = ESTILO[tec]
        if faixa:
            ax.fill_between(xs, [l[faixa[0]] for l in serie], [l[faixa[1]] for l in serie],
                            color=estilo["cor"], alpha=0.15, linewidth=0)
        ax.plot(xs, ys, color=estilo["cor"], linewidth=2.5, marker=estilo["marcador"],
                markersize=9, markeredgecolor=FUNDO, markeredgewidth=1.5,
                label=estilo["nome"], zorder=3)
        finais.append((xs[-1] + 0.08, ys[-1], tec))

    ax.set_xticks(posicoes, [str(n) for n in niveis])
    ax.set_xlim(-0.2, len(niveis) - 1 + 0.75)
    ax.set_xlabel("Usuários virtuais simultâneos (VUs)")
    ax.set_ylabel(titulo_y)
    if log:
        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    else:
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_formatter(FuncFormatter(milhar))
    ax.grid(axis="y", color=GRADE, linewidth=1)
    ax.set_axisbelow(True)
    ax.set_title(f"{TITULO_CARGA[carga]}{sufixo_titulo}", loc="left", fontsize=15, pad=14)
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.13), ncol=4, frameon=False)

    formato = (lambda v: f"{v:.1f} ms".replace(".", ",")) if log else milhar
    rotular_fim_das_linhas(ax, finais, formato)
    fig.tight_layout()
    fig.savefig(arquivo, facecolor=FUNDO)
    plt.close(fig)


def grafico_tamanho(linhas, arquivo):
    paineis = []
    for carga, titulo in [("leve", "Consulta pequena (carga leve)"),
                          ("pesada", "Listar 1000 músicas (carga pesada)")]:
        dados = {l["tecnologia"]: l for l in linhas
                 if l["carga"] == carga and int(l["vus"]) == 1}
        tecs = [t for t in ORDEM if t in dados]
        if tecs:
            paineis.append((titulo, tecs, dados))
    if not paineis:
        return
    fig, eixos = plt.subplots(1, len(paineis), figsize=(6 * len(paineis), 5.2), dpi=150)
    if len(paineis) == 1:
        eixos = [eixos]
    for ax, (titulo, tecs, dados) in zip(eixos, paineis):
        valores = [dados[t]["bytes_recebidos_por_req"] for t in tecs]
        y = list(range(len(tecs)))[::-1]
        ax.barh(y, valores, color=[ESTILO[t]["cor"] for t in tecs], height=0.6)
        ax.set_yticks(y, [ESTILO[t]["nome"] for t in tecs])
        ax.tick_params(axis="y", length=0, labelsize=13, labelcolor=TEXTO)
        maior = max(valores)
        for yi, v in zip(y, valores):
            texto = f"{v / 1024:.1f} KB".replace(".", ",") if v >= 1024 else f"{v:.0f} B"
            ax.text(v + maior * 0.02, yi, texto, va="center", fontsize=12, color=TEXTO)
        ax.set_xlim(0, maior * 1.25)
        ax.xaxis.set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.set_title(titulo, loc="left", fontsize=14, pad=10)
    fig.suptitle("Bytes recebidos por requisição (corpo + cabeçalhos)",
                 x=0.01, ha="left", fontsize=15, color=TEXTO)
    fig.tight_layout()
    fig.savefig(arquivo, facecolor=FUNDO)
    plt.close(fig)


def grafico_comparacao_linguagens(linhas, arquivo):
    """Compara vazão (req/s) de Python vs Node.js no maior nível de VUs."""
    max_vus = max(int(l["vus"]) for l in linhas)
    cargas = ["leve", "pesada", "escrita"]
    fig, eixos = plt.subplots(1, 3, figsize=(15, 5.2), dpi=150)
    for ax, carga in zip(eixos, cargas):
        xs = list(range(len(ORDEM)))
        larg = 0.36
        py_vals = [next((l["req_por_s"] for l in linhas if l["linguagem"] == "python"
                         and l["tecnologia"] == t and l["carga"] == carga
                         and int(l["vus"]) == max_vus), 0) for t in ORDEM]
        nd_vals = [next((l["req_por_s"] for l in linhas if l["linguagem"] == "node"
                         and l["tecnologia"] == t and l["carga"] == carga
                         and int(l["vus"]) == max_vus), 0) for t in ORDEM]
        ax.bar([x - larg / 2 for x in xs], py_vals, width=larg, label="Python", color="#2a78d6")
        ax.bar([x + larg / 2 for x in xs], nd_vals, width=larg, label="Node.js", color="#1baf7a")
        ax.set_xticks(xs, [ESTILO[t]["nome"] for t in ORDEM])
        ax.yaxis.set_major_formatter(FuncFormatter(milhar))
        ax.grid(axis="y", color=GRADE, linewidth=1)
        ax.set_axisbelow(True)
        ax.set_title(carga.capitalize(), loc="left", fontsize=14, pad=10)
    eixos[0].set_ylabel("Requisições por segundo (vazão)")
    eixos[0].legend(frameon=False)
    fig.suptitle(f"Python × Node.js — Vazão com {max_vus} usuários simultâneos",
                 x=0.01, ha="left", fontsize=15, color=TEXTO)
    fig.tight_layout()
    fig.savefig(arquivo, facecolor=FUNDO)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=RAIZ / "resultados" / "resultados.csv")
    parser.add_argument("--saida", type=Path, default=None)
    args = parser.parse_args()
    csv_path = args.csv.resolve()
    linhas = ler(csv_path)
    saida = args.saida.resolve() if args.saida is not None else csv_path.parent / "graficos"
    saida.mkdir(parents=True, exist_ok=True)

    linguagens = sorted({l["linguagem"] for l in linhas})
    for ling in linguagens:
        sub = [l for l in linhas if l["linguagem"] == ling]
        suf = "" if len(linguagens) == 1 else f"_{ling}"
        rotulo = "" if len(linguagens) == 1 else f" · {NOME_LING.get(ling, ling)}"
        for carga in TITULO_CARGA:
            grafico_linhas(sub, carga, "req_por_s", "Requisições por segundo (vazão)",
                           saida / f"vazao_{carga}{suf}.png", sufixo_titulo=rotulo,
                           faixa=("req_por_s_min", "req_por_s_max"))
            grafico_linhas(sub, carga, "latencia_p95_ms", "Latência p95 em ms (escala log)",
                           saida / f"latencia_p95_{carga}{suf}.png", sufixo_titulo=rotulo, log=True)
        grafico_tamanho(sub, saida / f"tamanho_respostas{suf}.png")

    if {"python", "node"}.issubset(linguagens):
        grafico_comparacao_linguagens(linhas, saida / "comparacao_linguagens.png")

    print(f"Gráficos salvos em {saida}")


if __name__ == "__main__":
    main()
