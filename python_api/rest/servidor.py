"""
Servidor REST (FastAPI).

Ideia central do REST: cada coisa é um RECURSO com uma URL, e o que fazer
com ele é dito pelo MÉTODO HTTP:
    GET    = consultar      POST = criar
    PUT    = alterar        DELETE = remover

Executar:  uv run uvicorn python_api.rest.servidor:app --port 8001
Documentação interativa gerada automaticamente: http://localhost:8001/docs
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from python_api.comum.dados import (DadosInvalidos, Musica, NaoEncontrado, Playlist,
                                    Usuario, criar_repositorio_populado)

app = FastAPI(title="Streaming de Músicas - REST")
repo = criar_repositorio_populado()


# ---- formato dos dados que o cliente envia (corpo das requisições) -------

class UsuarioEntrada(BaseModel):
    nome: str
    idade: int
    email: str


class MusicaEntrada(BaseModel):
    nome: str
    artista: str
    genero: str
    duracao_s: int


class PlaylistEntrada(BaseModel):
    nome: str
    descricao: str
    usuario_id: int
    musicas_ids: list[int]


class PlaylistAlteracao(BaseModel):
    nome: str
    descricao: str
    musicas_ids: list[int]


# ---- erros da camada de dados viram códigos de status HTTP --------------

@app.exception_handler(NaoEncontrado)
async def nao_encontrado(_: Request, erro: NaoEncontrado):
    return JSONResponse(status_code=404, content={"erro": str(erro)})


@app.exception_handler(DadosInvalidos)
async def dados_invalidos(_: Request, erro: DadosInvalidos):
    return JSONResponse(status_code=422, content={"erro": str(erro)})


# Obs.: as funções são "async def" porque o repositório fica na memória
# (não há espera por disco ou rede); assim o FastAPI as executa direto,
# sem passar por um pool de threads.

# ---- /usuarios ----------------------------------------------------------

@app.get("/usuarios")
async def listar_usuarios() -> list[Usuario]:
    return repo.listar_usuarios()


@app.post("/usuarios", status_code=201)
async def criar_usuario(dados: UsuarioEntrada) -> Usuario:
    return repo.criar_usuario(dados.nome, dados.idade, dados.email)


@app.get("/usuarios/{id}")
async def obter_usuario(id: int) -> Usuario:
    return repo.obter_usuario(id)


@app.put("/usuarios/{id}")
async def atualizar_usuario(id: int, dados: UsuarioEntrada) -> Usuario:
    return repo.atualizar_usuario(id, dados.nome, dados.idade, dados.email)


@app.delete("/usuarios/{id}", status_code=204)
async def remover_usuario(id: int) -> None:
    repo.remover_usuario(id)


@app.get("/usuarios/{id}/playlists")
async def playlists_do_usuario(id: int) -> list[Playlist]:
    return repo.playlists_do_usuario(id)


# ---- /musicas -----------------------------------------------------------

@app.get("/musicas")
async def listar_musicas() -> list[Musica]:
    return repo.listar_musicas()


@app.post("/musicas", status_code=201)
async def criar_musica(dados: MusicaEntrada) -> Musica:
    return repo.criar_musica(dados.nome, dados.artista, dados.genero, dados.duracao_s)


@app.get("/musicas/{id}")
async def obter_musica(id: int) -> Musica:
    return repo.obter_musica(id)


@app.put("/musicas/{id}")
async def atualizar_musica(id: int, dados: MusicaEntrada) -> Musica:
    return repo.atualizar_musica(id, dados.nome, dados.artista, dados.genero, dados.duracao_s)


@app.delete("/musicas/{id}", status_code=204)
async def remover_musica(id: int) -> None:
    repo.remover_musica(id)


@app.get("/musicas/{id}/playlists")
async def playlists_com_musica(id: int) -> list[Playlist]:
    return repo.playlists_com_musica(id)


# ---- /playlists ---------------------------------------------------------

@app.get("/playlists")
async def listar_playlists() -> list[Playlist]:
    return repo.listar_playlists()


@app.post("/playlists", status_code=201)
async def criar_playlist(dados: PlaylistEntrada) -> Playlist:
    return repo.criar_playlist(dados.nome, dados.descricao, dados.usuario_id, dados.musicas_ids)


@app.get("/playlists/{id}")
async def obter_playlist(id: int) -> Playlist:
    return repo.obter_playlist(id)


@app.put("/playlists/{id}")
async def atualizar_playlist(id: int, dados: PlaylistAlteracao) -> Playlist:
    return repo.atualizar_playlist(id, dados.nome, dados.descricao, dados.musicas_ids)


@app.delete("/playlists/{id}", status_code=204)
async def remover_playlist(id: int) -> None:
    repo.remover_playlist(id)


@app.get("/playlists/{id}/musicas")
async def musicas_da_playlist(id: int) -> list[Musica]:
    return repo.musicas_da_playlist(id)
