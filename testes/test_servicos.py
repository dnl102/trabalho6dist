"""
Testes de integração: sobem os 8 servidores (4 em Python + 4 em Node.js) e
verificam que TODOS se comportam EXATAMENTE igual (mesmas respostas, mesmos
erros, CRUD completo e regras de relacionamento).

Como os clientes Python conversam tanto com os servidores Python quanto com os
servidores Node.js, estes testes também provam interoperabilidade entre linguagens.

Executar:  uv run pytest -v
"""

import subprocess
from pathlib import Path

import pytest

from python_api.comum import servidores
from python_api.comum.dados import DadosInvalidos, NaoEncontrado, criar_repositorio_populado
from python_api.graphql.cliente import ClienteGraphQL
from python_api.grpc.cliente import ClienteGrpc
from python_api.rest.cliente import ClienteRest
from python_api.soap.cliente import ClienteSoap

RAIZ = Path(__file__).resolve().parent.parent

# 4 tecnologias em Python + 4 tecnologias em Node.js = 8 servidores
SERVIDORES_TESTADOS = [
    "rest", "graphql", "grpc", "soap",
    "rest_node", "graphql_node", "grpc_node", "soap_node",
]


@pytest.fixture(scope="module")
def clientes():
    """Sobe os 8 servidores (dados iniciais limpos) e conecta um cliente em cada."""
    processos = [servidores.iniciar(nome) for nome in SERVIDORES_TESTADOS]
    try:
        yield {
            "rest": ClienteRest("http://127.0.0.1:8001"),
            "graphql": ClienteGraphQL("http://127.0.0.1:8002/graphql"),
            "grpc": ClienteGrpc("127.0.0.1:50051"),
            "soap": ClienteSoap("http://127.0.0.1:8004/?wsdl"),
            "rest_node": ClienteRest("http://127.0.0.1:8101"),
            "graphql_node": ClienteGraphQL("http://127.0.0.1:8102/graphql"),
            "grpc_node": ClienteGrpc("127.0.0.1:50151"),
            "soap_node": ClienteSoap("http://127.0.0.1:8104/?wsdl"),
        }
    finally:
        for processo in processos:
            servidores.parar(processo)


@pytest.fixture(scope="module")
def esperado():
    """Um repositório local com os mesmos dados iniciais, para comparação."""
    return criar_repositorio_populado()


def como_dict(objeto):
    return dict(vars(objeto))


# ---- as 5 consultas do enunciado: os 8 servidores devem concordar -------
# (rodam antes dos testes de escrita, enquanto os dados ainda são os iniciais)

def test_listar_usuarios(clientes, esperado):
    referencia = [como_dict(u) for u in esperado.listar_usuarios()]
    for nome, cliente in clientes.items():
        assert cliente.listar_usuarios() == referencia, nome


def test_listar_musicas(clientes, esperado):
    referencia = [como_dict(m) for m in esperado.listar_musicas()]
    for nome, cliente in clientes.items():
        assert cliente.listar_musicas() == referencia, nome


@pytest.mark.parametrize("usuario_id", [1, 50, 100])
def test_playlists_do_usuario(clientes, esperado, usuario_id):
    referencia = [como_dict(p) for p in esperado.playlists_do_usuario(usuario_id)]
    for nome, cliente in clientes.items():
        assert cliente.playlists_do_usuario(usuario_id) == referencia, nome


@pytest.mark.parametrize("playlist_id", [1, 150, 300])
def test_musicas_da_playlist(clientes, esperado, playlist_id):
    referencia = [como_dict(m) for m in esperado.musicas_da_playlist(playlist_id)]
    for nome, cliente in clientes.items():
        assert cliente.musicas_da_playlist(playlist_id) == referencia, nome


@pytest.mark.parametrize("musica_id", [1, 176, 500, 1000])
def test_playlists_com_musica(clientes, esperado, musica_id):
    referencia = [como_dict(p) for p in esperado.playlists_com_musica(musica_id)]
    for nome, cliente in clientes.items():
        assert cliente.playlists_com_musica(musica_id) == referencia, nome


def test_listar_playlists(clientes, esperado):
    referencia = [como_dict(p) for p in esperado.listar_playlists()]
    for nome, cliente in clientes.items():
        assert cliente.listar_playlists() == referencia, nome


# ---- erros: devem ser equivalentes em todos os 8 servidores -------------

@pytest.mark.parametrize("alvo", SERVIDORES_TESTADOS)
def test_recurso_inexistente(clientes, alvo):
    cliente = clientes[alvo]
    with pytest.raises(NaoEncontrado):
        cliente.obter_usuario(9999)
    with pytest.raises(NaoEncontrado):
        cliente.obter_musica(9999)
    with pytest.raises(NaoEncontrado):
        cliente.musicas_da_playlist(9999)
    with pytest.raises(NaoEncontrado):
        cliente.remover_usuario(9999)


@pytest.mark.parametrize("alvo", SERVIDORES_TESTADOS)
def test_dados_invalidos(clientes, alvo):
    cliente = clientes[alvo]
    with pytest.raises(DadosInvalidos):
        cliente.criar_playlist("Vazia", "Sem músicas", 1, [])       # playlist sem músicas
    with pytest.raises(DadosInvalidos):
        cliente.criar_playlist("X", "Desc", 9999, [1])              # dono inexistente
    with pytest.raises(DadosInvalidos):
        cliente.criar_playlist("X", "Desc", 1, [99999])             # música inexistente
    with pytest.raises(DadosInvalidos):
        cliente.criar_usuario("", 20, "a@b.com")                    # nome vazio
    with pytest.raises(DadosInvalidos):
        cliente.criar_usuario("Ana", 20, "email_invalido")          # email sem @
    with pytest.raises(DadosInvalidos):
        cliente.criar_musica("M", "Art", "MPB", 0)                  # duração <= 0


# ---- CRUD completo, em cada um dos 8 servidores -------------------------

@pytest.mark.parametrize("alvo", SERVIDORES_TESTADOS)
def test_crud_usuario(clientes, alvo):
    cliente = clientes[alvo]
    criado = cliente.criar_usuario("Teste", 30, "teste@streaming.com")
    assert cliente.obter_usuario(criado["id"]) == {
        "id": criado["id"], "nome": "Teste", "idade": 30, "email": "teste@streaming.com",
    }
    cliente.atualizar_usuario(criado["id"], "Teste 2", 31, "teste2@streaming.com")
    assert cliente.obter_usuario(criado["id"]) == {
        "id": criado["id"], "nome": "Teste 2", "idade": 31, "email": "teste2@streaming.com",
    }
    cliente.remover_usuario(criado["id"])
    with pytest.raises(NaoEncontrado):
        cliente.obter_usuario(criado["id"])


@pytest.mark.parametrize("alvo", SERVIDORES_TESTADOS)
def test_crud_musica(clientes, alvo):
    cliente = clientes[alvo]
    criada = cliente.criar_musica("Aquarela", "Toquinho", "MPB", 254)
    assert cliente.obter_musica(criada["id"]) == {
        "id": criada["id"], "nome": "Aquarela", "artista": "Toquinho",
        "genero": "MPB", "duracao_s": 254,
    }
    cliente.atualizar_musica(criada["id"], "Aquarela", "Toquinho e Vinicius", "Bossa Nova", 260)
    assert cliente.obter_musica(criada["id"])["genero"] == "Bossa Nova"
    assert cliente.obter_musica(criada["id"])["duracao_s"] == 260
    cliente.remover_musica(criada["id"])
    with pytest.raises(NaoEncontrado):
        cliente.obter_musica(criada["id"])


@pytest.mark.parametrize("alvo", SERVIDORES_TESTADOS)
def test_crud_playlist(clientes, alvo):
    cliente = clientes[alvo]
    dono = cliente.criar_usuario("Dono", 20, "dono@streaming.com")
    criada = cliente.criar_playlist("Minha", "Desc inicial", dono["id"], [3, 1, 2])
    assert criada["musicas_ids"] == [3, 1, 2]
    assert criada["descricao"] == "Desc inicial"
    assert cliente.playlists_do_usuario(dono["id"]) == [criada]

    alterada = cliente.atualizar_playlist(criada["id"], "Minha (nova)", "Desc nova", [5])
    assert alterada == {
        "id": criada["id"], "nome": "Minha (nova)", "descricao": "Desc nova",
        "usuario_id": dono["id"], "musicas_ids": [5],
    }
    assert [m["id"] for m in cliente.musicas_da_playlist(criada["id"])] == [5]

    cliente.remover_playlist(criada["id"])
    assert cliente.playlists_do_usuario(dono["id"]) == []
    cliente.remover_usuario(dono["id"])


# ---- regras de relacionamento do diagrama -------------------------------

@pytest.mark.parametrize("alvo", SERVIDORES_TESTADOS)
def test_remover_usuario_remove_suas_playlists(clientes, alvo):
    cliente = clientes[alvo]
    dono = cliente.criar_usuario("Dono", 20, "dono@streaming.com")
    playlist = cliente.criar_playlist("P", "Desc", dono["id"], [1])
    cliente.remover_usuario(dono["id"])
    with pytest.raises(NaoEncontrado):
        cliente.musicas_da_playlist(playlist["id"])


@pytest.mark.parametrize("alvo", SERVIDORES_TESTADOS)
def test_remover_musica_tira_ela_das_playlists(clientes, alvo):
    cliente = clientes[alvo]
    dono = cliente.criar_usuario("Dono", 20, "dono@streaming.com")
    m1 = cliente.criar_musica("M1", "A", "MPB", 180)
    m2 = cliente.criar_musica("M2", "B", "Rock", 200)
    com_duas = cliente.criar_playlist("Duas", "Duas músicas", dono["id"], [m1["id"], m2["id"]])
    so_uma = cliente.criar_playlist("Uma", "Só uma", dono["id"], [m1["id"]])

    cliente.remover_musica(m1["id"])

    assert [m["id"] for m in cliente.musicas_da_playlist(com_duas["id"])] == [m2["id"]]
    with pytest.raises(NaoEncontrado):
        cliente.musicas_da_playlist(so_uma["id"])
    cliente.remover_usuario(dono["id"])


# ---- clientes Node.js (falam com Node.js E também com Python!) ----------

@pytest.mark.parametrize("script, destino", [
    ("node_api/rest/cliente.js", "http://127.0.0.1:8101"),
    ("node_api/graphql/cliente.js", "http://127.0.0.1:8102/graphql"),
    ("node_api/grpc/cliente.js", "127.0.0.1:50151"),
    ("node_api/soap/cliente.js", "http://127.0.0.1:8104/?wsdl"),
    # Interoperabilidade inversa: cliente Node.js -> servidor Python
    ("node_api/rest/cliente.js", "http://127.0.0.1:8001"),
    ("node_api/graphql/cliente.js", "http://127.0.0.1:8002/graphql"),
    ("node_api/grpc/cliente.js", "127.0.0.1:50051"),
    ("node_api/soap/cliente.js", "http://127.0.0.1:8004/?wsdl"),
])
def test_clientes_node_funcionam(clientes, script, destino):
    resultado = subprocess.run(["node", script, destino], cwd=RAIZ, capture_output=True, text=True)
    assert resultado.returncode == 0, resultado.stderr
    assert "CRUD de exemplo:" in resultado.stdout
