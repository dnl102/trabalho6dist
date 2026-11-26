"""
Cliente REST: usa a biblioteca "requests" para fazer requisições HTTP.
Cada operação = (método HTTP, URL). Os dados vão e voltam em JSON.

Executar (com o servidor no ar):  uv run python -m python_api.rest.cliente
"""

import requests

from python_api.comum.dados import DadosInvalidos, NaoEncontrado

URL = "http://localhost:8001"


class ClienteRest:
    def __init__(self, url=URL):
        self.url = url
        self.http = requests.Session()  # reaproveita a conexão TCP

    @staticmethod
    def _mensagem_erro(resposta):
        try:
            corpo = resposta.json()
        except ValueError:
            return resposta.text
        if isinstance(corpo, dict) and "erro" in corpo:
            return str(corpo["erro"])
        return resposta.text

    def _chamar(self, metodo, caminho, corpo=None):
        resposta = self.http.request(metodo, self.url + caminho, json=corpo)
        if resposta.status_code == 404:
            raise NaoEncontrado(self._mensagem_erro(resposta))
        if resposta.status_code == 422:
            raise DadosInvalidos(self._mensagem_erro(resposta))
        resposta.raise_for_status()
        return resposta.json() if resposta.content else None

    # ---- as 5 consultas do enunciado --------------------------------------
    def listar_usuarios(self):
        return self._chamar("GET", "/usuarios")

    def listar_musicas(self):
        return self._chamar("GET", "/musicas")

    def playlists_do_usuario(self, usuario_id):
        return self._chamar("GET", f"/usuarios/{usuario_id}/playlists")

    def musicas_da_playlist(self, playlist_id):
        return self._chamar("GET", f"/playlists/{playlist_id}/musicas")

    def playlists_com_musica(self, musica_id):
        return self._chamar("GET", f"/musicas/{musica_id}/playlists")

    # ---- usuários ---------------------------------------------------------
    def obter_usuario(self, id):
        return self._chamar("GET", f"/usuarios/{id}")

    def criar_usuario(self, nome, idade, email):
        return self._chamar("POST", "/usuarios", {"nome": nome, "idade": idade, "email": email})

    def atualizar_usuario(self, id, nome, idade, email):
        return self._chamar("PUT", f"/usuarios/{id}", {"nome": nome, "idade": idade, "email": email})

    def remover_usuario(self, id):
        self._chamar("DELETE", f"/usuarios/{id}")

    # ---- músicas ----------------------------------------------------------
    def obter_musica(self, id):
        return self._chamar("GET", f"/musicas/{id}")

    def criar_musica(self, nome, artista, genero, duracao_s):
        return self._chamar("POST", "/musicas", {
            "nome": nome, "artista": artista, "genero": genero, "duracao_s": duracao_s})

    def atualizar_musica(self, id, nome, artista, genero, duracao_s):
        return self._chamar("PUT", f"/musicas/{id}", {
            "nome": nome, "artista": artista, "genero": genero, "duracao_s": duracao_s})

    def remover_musica(self, id):
        self._chamar("DELETE", f"/musicas/{id}")

    # ---- playlists --------------------------------------------------------
    def listar_playlists(self):
        return self._chamar("GET", "/playlists")

    def obter_playlist(self, id):
        return self._chamar("GET", f"/playlists/{id}")

    def criar_playlist(self, nome, descricao, usuario_id, musicas_ids):
        return self._chamar("POST", "/playlists", {
            "nome": nome, "descricao": descricao,
            "usuario_id": usuario_id, "musicas_ids": musicas_ids})

    def atualizar_playlist(self, id, nome, descricao, musicas_ids):
        return self._chamar("PUT", f"/playlists/{id}", {
            "nome": nome, "descricao": descricao, "musicas_ids": musicas_ids})

    def remover_playlist(self, id):
        self._chamar("DELETE", f"/playlists/{id}")


if __name__ == "__main__":
    from python_api.comum.demonstracao import demonstrar
    demonstrar(ClienteRest(), "REST")
