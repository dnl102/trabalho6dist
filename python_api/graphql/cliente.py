"""
Cliente GraphQL: toda requisição é um POST para /graphql com uma "query"
em texto. O cliente escolhe os campos que quer receber. Note como uma
consulta como "playlists do usuário" é feita navegando pela relação
usuario -> playlists, em vez de usar uma URL própria.

Executar (com o servidor no ar):  uv run python -m python_api.graphql.cliente
"""

import requests

from python_api.comum.dados import DadosInvalidos, NaoEncontrado

URL = "http://localhost:8002/graphql"

# Campos pedidos para cada tipo. O cliente decide o que vem na resposta:
# aqui pedimos tudo para ficar igual aos outros serviços.
USUARIO = "id nome idade email"
MUSICA = "id nome artista genero duracaoS"
PLAYLIST = "id nome descricao usuario { id } musicas { id }"


def _musica(m):
    """Converte o campo camelCase (duracaoS) do GraphQL para o formato comum."""
    return {"id": m["id"], "nome": m["nome"], "artista": m["artista"],
            "genero": m["genero"], "duracao_s": m["duracaoS"]}


def _playlist(p):
    """Converte a playlist do formato GraphQL para o formato comum."""
    return {"id": p["id"], "nome": p["nome"], "descricao": p["descricao"],
            "usuario_id": p["usuario"]["id"],
            "musicas_ids": [m["id"] for m in p["musicas"]]}


class ClienteGraphQL:
    def __init__(self, url=URL):
        self.url = url
        self.http = requests.Session()

    def _executar(self, query, variaveis=None):
        resposta = self.http.post(self.url, json={"query": query, "variables": variaveis or {}})
        try:
            corpo = resposta.json()
        except ValueError:
            resposta.raise_for_status()
            raise
        if corpo.get("errors"):
            erro = corpo["errors"][0]
            codigo = (erro.get("extensions") or {}).get("codigo")
            if codigo == "NAO_ENCONTRADO":
                raise NaoEncontrado(erro["message"])
            if codigo == "DADOS_INVALIDOS" or resposta.status_code == 400:
                raise DadosInvalidos(erro["message"])
            raise RuntimeError(erro["message"])
        resposta.raise_for_status()
        return corpo["data"]

    # ---- as 5 consultas do enunciado --------------------------------------
    def listar_usuarios(self):
        return self._executar(f"{{ usuarios {{ {USUARIO} }} }}")["usuarios"]

    def listar_musicas(self):
        return [_musica(m) for m in self._executar(f"{{ musicas {{ {MUSICA} }} }}")["musicas"]]

    def playlists_do_usuario(self, usuario_id):
        dados = self._executar(
            f"query($id: Int!) {{ usuario(id: $id) {{ playlists {{ {PLAYLIST} }} }} }}",
            {"id": usuario_id})
        return [_playlist(p) for p in dados["usuario"]["playlists"]]

    def musicas_da_playlist(self, playlist_id):
        dados = self._executar(
            f"query($id: Int!) {{ playlist(id: $id) {{ musicas {{ {MUSICA} }} }} }}",
            {"id": playlist_id})
        return [_musica(m) for m in dados["playlist"]["musicas"]]

    def playlists_com_musica(self, musica_id):
        dados = self._executar(
            f"query($id: Int!) {{ musica(id: $id) {{ playlists {{ {PLAYLIST} }} }} }}",
            {"id": musica_id})
        return [_playlist(p) for p in dados["musica"]["playlists"]]

    # ---- usuários ---------------------------------------------------------
    def obter_usuario(self, id):
        return self._executar(f"query($id: Int!) {{ usuario(id: $id) {{ {USUARIO} }} }}",
                              {"id": id})["usuario"]

    def criar_usuario(self, nome, idade, email):
        return self._executar(
            f"mutation($nome: String!, $idade: Int!, $email: String!) "
            f"{{ criarUsuario(nome: $nome, idade: $idade, email: $email) {{ {USUARIO} }} }}",
            {"nome": nome, "idade": idade, "email": email})["criarUsuario"]

    def atualizar_usuario(self, id, nome, idade, email):
        return self._executar(
            f"mutation($id: Int!, $nome: String!, $idade: Int!, $email: String!) "
            f"{{ atualizarUsuario(id: $id, nome: $nome, idade: $idade, email: $email) {{ {USUARIO} }} }}",
            {"id": id, "nome": nome, "idade": idade, "email": email})["atualizarUsuario"]

    def remover_usuario(self, id):
        self._executar("mutation($id: Int!) { removerUsuario(id: $id) }", {"id": id})

    # ---- músicas ----------------------------------------------------------
    def obter_musica(self, id):
        return _musica(self._executar(f"query($id: Int!) {{ musica(id: $id) {{ {MUSICA} }} }}",
                                      {"id": id})["musica"])

    def criar_musica(self, nome, artista, genero, duracao_s):
        return _musica(self._executar(
            f"mutation($nome: String!, $artista: String!, $genero: String!, $duracaoS: Int!) "
            f"{{ criarMusica(nome: $nome, artista: $artista, genero: $genero, duracaoS: $duracaoS) {{ {MUSICA} }} }}",
            {"nome": nome, "artista": artista, "genero": genero, "duracaoS": duracao_s})["criarMusica"])

    def atualizar_musica(self, id, nome, artista, genero, duracao_s):
        return _musica(self._executar(
            f"mutation($id: Int!, $nome: String!, $artista: String!, $genero: String!, $duracaoS: Int!) "
            f"{{ atualizarMusica(id: $id, nome: $nome, artista: $artista, genero: $genero, duracaoS: $duracaoS) {{ {MUSICA} }} }}",
            {"id": id, "nome": nome, "artista": artista, "genero": genero, "duracaoS": duracao_s})["atualizarMusica"])

    def remover_musica(self, id):
        self._executar("mutation($id: Int!) { removerMusica(id: $id) }", {"id": id})

    # ---- playlists --------------------------------------------------------
    def listar_playlists(self):
        return [_playlist(p) for p in
                self._executar(f"{{ playlists {{ {PLAYLIST} }} }}")["playlists"]]

    def obter_playlist(self, id):
        return _playlist(self._executar(
            f"query($id: Int!) {{ playlist(id: $id) {{ {PLAYLIST} }} }}", {"id": id})["playlist"])

    def criar_playlist(self, nome, descricao, usuario_id, musicas_ids):
        return _playlist(self._executar(
            f"mutation($nome: String!, $descricao: String!, $usuarioId: Int!, $musicasIds: [Int!]!) "
            f"{{ criarPlaylist(nome: $nome, descricao: $descricao, usuarioId: $usuarioId, musicasIds: $musicasIds) "
            f"{{ {PLAYLIST} }} }}",
            {"nome": nome, "descricao": descricao,
             "usuarioId": usuario_id, "musicasIds": musicas_ids})["criarPlaylist"])

    def atualizar_playlist(self, id, nome, descricao, musicas_ids):
        return _playlist(self._executar(
            f"mutation($id: Int!, $nome: String!, $descricao: String!, $musicasIds: [Int!]!) "
            f"{{ atualizarPlaylist(id: $id, nome: $nome, descricao: $descricao, musicasIds: $musicasIds) "
            f"{{ {PLAYLIST} }} }}",
            {"id": id, "nome": nome, "descricao": descricao,
             "musicasIds": musicas_ids})["atualizarPlaylist"])

    def remover_playlist(self, id):
        self._executar("mutation($id: Int!) { removerPlaylist(id: $id) }", {"id": id})


if __name__ == "__main__":
    from python_api.comum.demonstracao import demonstrar
    demonstrar(ClienteGraphQL(), "GraphQL")
