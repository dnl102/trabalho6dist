"""
Sobe os 8 servidores (4 tecnologias em Python + 4 em Node.js).

Uso:
    uv run python -m python_api.comum.servidores                 # sobe os 8 (Ctrl+C encerra)
    uv run python -m python_api.comum.servidores rest rest_node  # sobe só os escolhidos

Cada servidor roda em 1 processo atendendo requisições (para manter
a comparação justa). Os modelos internos de concorrência variam conforme a
biblioteca: uvicorn usa 1 thread async (REST/GraphQL Python), gRPC e SOAP
Python usam pool de 10 threads, e todos os servidores Node.js usam 1 event loop.
"""

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent

# nome -> (porta, comando completo)
SERVIDORES = {
    # ---- Python (portas 8001, 8002, 50051, 8004) -------------------------
    # 1 processo, 1 thread (laço de eventos async do uvicorn)
    "rest": (8001, [sys.executable, "-m", "uvicorn", "python_api.rest.servidor:app", "--port", "8001",
                    "--log-level", "warning", "--no-access-log"]),
    # 1 processo, 1 thread (laço de eventos async do uvicorn)
    "graphql": (8002, [sys.executable, "-m", "uvicorn", "python_api.graphql.servidor:app", "--port", "8002",
                       "--log-level", "warning", "--no-access-log"]),
    # 1 processo, pool de 10 threads (definido em python_api/grpc/servidor.py)
    "grpc": (50051, [sys.executable, "-m", "python_api.grpc.servidor"]),
    # 1 worker (10 threads gthread) + processo supervisor do gunicorn
    "soap": (8004, [sys.executable, "-m", "gunicorn", "-k", "gthread", "-w", "1", "--threads", "10",
                    "-b", "127.0.0.1:8004", "--log-level", "warning",
                    "python_api.soap.servidor:app"]),

    # ---- Node.js (portas 8101, 8102, 50151, 8104) ------------------------
    # Todos em 1 processo Node.js (event loop single-thread da libuv)
    "rest_node": (8101, ["node", "node_api/rest/servidor.js"]),
    "graphql_node": (8102, ["node", "node_api/graphql/servidor.js"]),
    "grpc_node": (50151, ["node", "node_api/grpc/servidor.js"]),
    "soap_node": (8104, ["node", "node_api/soap/servidor.js"]),
}


def _porta_aberta(porta):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", porta)) == 0


def iniciar(nome, cpus=None, saida=None):
    """Inicia um servidor e espera ele aceitar conexões.
    cpus: lista de núcleos para fixar o processo (ex.: [2]), opcional."""
    porta, comando = SERVIDORES[nome]
    if _porta_aberta(porta):
        raise RuntimeError(f"A porta {porta} já está em uso (servidor {nome} já rodando?)")
    comando = list(comando)
    if cpus is not None:
        comando = ["taskset", "-c", ",".join(map(str, cpus)), *comando]
    processo = subprocess.Popen(comando, cwd=RAIZ, stdout=saida, stderr=saida,
                                start_new_session=True)
    for _ in range(100):
        if _porta_aberta(porta):
            return processo
        if processo.poll() is not None:
            raise RuntimeError(f"O servidor {nome} terminou ao iniciar")
        time.sleep(0.1)
    parar(processo)
    raise RuntimeError(f"O servidor {nome} não respondeu na porta {porta}")


def parar(processo):
    if processo.poll() is None:
        os.killpg(processo.pid, signal.SIGTERM)
        try:
            processo.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(processo.pid, signal.SIGKILL)
            processo.wait()


def _encerrar(*_):
    # Ignora sinais repetidos (o "uv run" repassa o mesmo sinal) para não
    # interromper o desligamento dos servidores no meio.
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    raise KeyboardInterrupt


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _encerrar)  # "kill" também encerra tudo
    signal.signal(signal.SIGINT, _encerrar)   # Ctrl+C
    nomes = sys.argv[1:] or list(SERVIDORES)
    processos = []
    try:
        for nome in nomes:
            processos.append(iniciar(nome))
            print(f"{nome:12} -> porta {SERVIDORES[nome][0]}", flush=True)
        print("Servidores no ar. Ctrl+C para encerrar.", flush=True)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for p in processos:
            parar(p)
