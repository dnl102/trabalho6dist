"""
Servidor GraphQL (Strawberry).

Ideia central do GraphQL: existe UM ÚNICO endereço (/graphql). O cliente
manda uma "query" dizendo exatamente quais campos quer, e pode navegar
pelas relações (usuário -> playlists -> músicas) numa só requisição.
    query    = consultar
    mutation = criar / alterar / remover

Executar:  uv run uvicorn python_api.graphql.servidor:app --port 8002
Interface para testar queries no navegador: http://localhost:8002/graphql
"""

import strawberry
from graphql import GraphQLError
from strawberry.asgi import GraphQL

from python_api.comum import dados
from python_api.comum.dados import DadosInvalidos, NaoEncontrado, criar_repositorio_populado

repo = criar_repositorio_populado()


def traduzir_erros(funcao):
    """Executa a função e transforma erros da camada de dados em erros
    GraphQL, com um código em 'extensions' para o cliente identificar."""
    try:
        return funcao()
    except NaoEncontrado as erro:
        raise GraphQLError(str(erro), extensions={"codigo": "NAO_ENCONTRADO"})
    except DadosInvalidos as erro:
        raise GraphQLError(str(erro), extensions={"codigo": "DADOS_INVALIDOS"})


# ---- tipos do esquema ----------------------------------------------------
# Cada tipo diz quais campos existem. Os campos de relação (ex.: playlists
# de um usuário) são funções: só são calculados se o cliente pedir.

@strawberry.type
class Usuario:
    id: int
    nome: str
    idade: int
    email: str

    @strawberry.field
    def playlists(self) -> list["Playlist"]:
        return [Playlist.de(p) for p in repo.playlists_do_usuario(self.id)]

    @staticmethod
    def de(u: dados.Usuario) -> "Usuario":
        return Usuario(id=u.id, nome=u.nome, idade=u.idade, email=u.email)


@strawberry.type
class Musica:
    id: int
    nome: str
    artista: str
    genero: str
    duracao_s: int

    @strawberry.field
    def playlists(self) -> list["Playlist"]:
        return [Playlist.de(p) for p in repo.playlists_com_musica(self.id)]

    @staticmethod
    def de(m: dados.Musica) -> "Musica":
        return Musica(id=m.id, nome=m.nome, artista=m.artista,
                      genero=m.genero, duracao_s=m.duracao_s)


@strawberry.type
class Playlist:
    id: int
    nome: str
    descricao: str
    usuario_id: strawberry.Private[int]  # interno: o cliente usa o campo "usuario"

    @strawberry.field
    def usuario(self) -> Usuario:
        return Usuario.de(repo.obter_usuario(self.usuario_id))

    @strawberry.field
    def musicas(self) -> list[Musica]:
        return [Musica.de(m) for m in repo.musicas_da_playlist(self.id)]

    @staticmethod
    def de(p: dados.Playlist) -> "Playlist":
        return Playlist(id=p.id, nome=p.nome, descricao=p.descricao, usuario_id=p.usuario_id)


# ---- consultas (Query) ---------------------------------------------------

@strawberry.type
class Query:
    @strawberry.field
    def usuarios(self) -> list[Usuario]:
        return [Usuario.de(u) for u in repo.listar_usuarios()]

    @strawberry.field
    def usuario(self, id: int) -> Usuario:
        return traduzir_erros(lambda: Usuario.de(repo.obter_usuario(id)))

    @strawberry.field
    def musicas(self) -> list[Musica]:
        return [Musica.de(m) for m in repo.listar_musicas()]

    @strawberry.field
    def musica(self, id: int) -> Musica:
        return traduzir_erros(lambda: Musica.de(repo.obter_musica(id)))

    @strawberry.field
    def playlists(self) -> list[Playlist]:
        return [Playlist.de(p) for p in repo.listar_playlists()]

    @strawberry.field
    def playlist(self, id: int) -> Playlist:
        return traduzir_erros(lambda: Playlist.de(repo.obter_playlist(id)))


# ---- alterações (Mutation) -----------------------------------------------

@strawberry.type
class Mutation:
    @strawberry.mutation
    def criar_usuario(self, nome: str, idade: int, email: str) -> Usuario:
        return traduzir_erros(lambda: Usuario.de(repo.criar_usuario(nome, idade, email)))

    @strawberry.mutation
    def atualizar_usuario(self, id: int, nome: str, idade: int, email: str) -> Usuario:
        return traduzir_erros(lambda: Usuario.de(repo.atualizar_usuario(id, nome, idade, email)))

    @strawberry.mutation
    def remover_usuario(self, id: int) -> bool:
        traduzir_erros(lambda: repo.remover_usuario(id))
        return True

    @strawberry.mutation
    def criar_musica(self, nome: str, artista: str, genero: str, duracao_s: int) -> Musica:
        return traduzir_erros(lambda: Musica.de(repo.criar_musica(nome, artista, genero, duracao_s)))

    @strawberry.mutation
    def atualizar_musica(self, id: int, nome: str, artista: str, genero: str, duracao_s: int) -> Musica:
        return traduzir_erros(lambda: Musica.de(
            repo.atualizar_musica(id, nome, artista, genero, duracao_s)))

    @strawberry.mutation
    def remover_musica(self, id: int) -> bool:
        traduzir_erros(lambda: repo.remover_musica(id))
        return True

    @strawberry.mutation
    def criar_playlist(self, nome: str, descricao: str,
                       usuario_id: int, musicas_ids: list[int]) -> Playlist:
        return traduzir_erros(
            lambda: Playlist.de(repo.criar_playlist(nome, descricao, usuario_id, musicas_ids)))

    @strawberry.mutation
    def atualizar_playlist(self, id: int, nome: str, descricao: str,
                           musicas_ids: list[int]) -> Playlist:
        return traduzir_erros(
            lambda: Playlist.de(repo.atualizar_playlist(id, nome, descricao, musicas_ids)))

    @strawberry.mutation
    def remover_playlist(self, id: int) -> bool:
        traduzir_erros(lambda: repo.remover_playlist(id))
        return True


schema = strawberry.Schema(query=Query, mutation=Mutation)
app = GraphQL(schema)
