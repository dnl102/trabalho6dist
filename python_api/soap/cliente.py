"""
Cliente SOAP (zeep): o zeep lê o contrato WSDL do servidor e cria
automaticamente os métodos client.service.<Operação>(...). Por baixo, cada
chamada vira um envelope XML enviado por HTTP POST.

Executar (com o servidor no ar):  uv run python -m python_api.soap.cliente
"""

import zeep
from zeep.exceptions import Fault

from python_api.comum.dados import DadosInvalidos, NaoEncontrado

WSDL = "http://localhost:8004/?wsdl"


# ---- conversão: objetos do zeep -> dicionários (formato comum) ----------

def _usuario(u):
    return {"id": u.id, "nome": u.nome, "idade": u.idade, "email": u.email}


def _musica(m):
    return {"id": m.id, "nome": m.nome, "artista": m.artista,
            "genero": m.genero, "duracao_s": m.duracao_s}


def _playlist(p):
    # No XML, a lista de ids vem como <musicas_ids><integer>..</integer></musicas_ids>
    ids = p.musicas_ids.integer if p.musicas_ids is not None else []
    return {"id": p.id, "nome": p.nome, "descricao": p.descricao,
            "usuario_id": p.usuario_id, "musicas_ids": list(ids)}


def _lista(resposta):
    """O zeep devolve None quando a lista vem vazia; normaliza para []."""
    return resposta or []


class ClienteSoap:
    def __init__(self, wsdl=WSDL):
        self.servico = zeep.Client(wsdl).service

    def _chamar(self, operacao, *args):
        try:
            return getattr(self.servico, operacao)(*args)
        except Fault as erro:
            # Remove prefixo XML (ex.: "soap11env:Client.NaoEncontrado" -> "Client.NaoEncontrado")
            codigo = (erro.code or "").split(":")[-1]
            if codigo.endswith("NaoEncontrado"):
                raise NaoEncontrado(erro.message) from None
            if codigo.endswith("DadosInvalidos") or codigo.startswith("Client.") or codigo == "Client":
                raise DadosInvalidos(erro.message) from None
            raise

    # ---- as 5 consultas do enunciado --------------------------------------
    def listar_usuarios(self):
        return [_usuario(u) for u in _lista(self._chamar("ListarUsuarios"))]

    def listar_musicas(self):
        return [_musica(m) for m in _lista(self._chamar("ListarMusicas"))]

    def playlists_do_usuario(self, usuario_id):
        resposta = self._chamar("PlaylistsDoUsuario", usuario_id)
        return [_playlist(p) for p in _lista(resposta)]

    def musicas_da_playlist(self, playlist_id):
        resposta = self._chamar("MusicasDaPlaylist", playlist_id)
        return [_musica(m) for m in _lista(resposta)]

    def playlists_com_musica(self, musica_id):
        resposta = self._chamar("PlaylistsComMusica", musica_id)
        return [_playlist(p) for p in _lista(resposta)]

    # ---- usuários ---------------------------------------------------------
    def obter_usuario(self, id):
        return _usuario(self._chamar("ObterUsuario", id))

    def criar_usuario(self, nome, idade, email):
        return _usuario(self._chamar("CriarUsuario", nome, idade, email))

    def atualizar_usuario(self, id, nome, idade, email):
        return _usuario(self._chamar("AtualizarUsuario", id, nome, idade, email))

    def remover_usuario(self, id):
        self._chamar("RemoverUsuario", id)

    # ---- músicas ----------------------------------------------------------
    def obter_musica(self, id):
        return _musica(self._chamar("ObterMusica", id))

    def criar_musica(self, nome, artista, genero, duracao_s):
        return _musica(self._chamar("CriarMusica", nome, artista, genero, duracao_s))

    def atualizar_musica(self, id, nome, artista, genero, duracao_s):
        return _musica(self._chamar("AtualizarMusica", id, nome, artista, genero, duracao_s))

    def remover_musica(self, id):
        self._chamar("RemoverMusica", id)

    # ---- playlists --------------------------------------------------------
    def listar_playlists(self):
        return [_playlist(p) for p in _lista(self._chamar("ListarPlaylists"))]

    def obter_playlist(self, id):
        return _playlist(self._chamar("ObterPlaylist", id))

    def criar_playlist(self, nome, descricao, usuario_id, musicas_ids):
        return _playlist(self._chamar("CriarPlaylist", nome, descricao, usuario_id,
                                      {"integer": musicas_ids}))

    def atualizar_playlist(self, id, nome, descricao, musicas_ids):
        return _playlist(self._chamar("AtualizarPlaylist", id, nome, descricao,
                                      {"integer": musicas_ids}))

    def remover_playlist(self, id):
        self._chamar("RemoverPlaylist", id)


if __name__ == "__main__":
    from python_api.comum.demonstracao import demonstrar
    demonstrar(ClienteSoap(), "SOAP")
