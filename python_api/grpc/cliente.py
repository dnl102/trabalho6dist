"""
Cliente gRPC: o "stub" (gerado a partir do .proto) tem um método para cada
rpc do serviço. Chamar stub.ObterUsuario(...) parece uma chamada local, mas
a mensagem é serializada em binário e enviada ao servidor via HTTP/2.

Executar (com o servidor no ar):  uv run python -m python_api.grpc.cliente
"""

import grpc

from python_api.comum.dados import DadosInvalidos, NaoEncontrado
from python_api.grpc import musica_pb2 as pb
from python_api.grpc import musica_pb2_grpc as pb_grpc

ENDERECO = "localhost:50051"


# ---- conversão: mensagens protobuf -> dicionários (formato comum) -------

def _usuario(u):
    return {"id": u.id, "nome": u.nome, "idade": u.idade, "email": u.email}


def _musica(m):
    return {"id": m.id, "nome": m.nome, "artista": m.artista,
            "genero": m.genero, "duracao_s": m.duracao_s}


def _playlist(p):
    return {"id": p.id, "nome": p.nome, "descricao": p.descricao,
            "usuario_id": p.usuario_id, "musicas_ids": list(p.musicas_ids)}


class ClienteGrpc:
    def __init__(self, endereco=ENDERECO):
        self.canal = grpc.insecure_channel(endereco)
        self.stub = pb_grpc.StreamingStub(self.canal)

    def _chamar(self, metodo, requisicao):
        try:
            return metodo(requisicao)
        except grpc.RpcError as erro:
            if erro.code() == grpc.StatusCode.NOT_FOUND:
                raise NaoEncontrado(erro.details()) from None
            if erro.code() == grpc.StatusCode.INVALID_ARGUMENT:
                raise DadosInvalidos(erro.details()) from None
            raise

    # ---- as 5 consultas do enunciado --------------------------------------
    def listar_usuarios(self):
        return [_usuario(u) for u in self._chamar(self.stub.ListarUsuarios, pb.Vazio()).usuarios]

    def listar_musicas(self):
        return [_musica(m) for m in self._chamar(self.stub.ListarMusicas, pb.Vazio()).musicas]

    def playlists_do_usuario(self, usuario_id):
        resposta = self._chamar(self.stub.PlaylistsDoUsuario, pb.Id(id=usuario_id))
        return [_playlist(p) for p in resposta.playlists]

    def musicas_da_playlist(self, playlist_id):
        resposta = self._chamar(self.stub.MusicasDaPlaylist, pb.Id(id=playlist_id))
        return [_musica(m) for m in resposta.musicas]

    def playlists_com_musica(self, musica_id):
        resposta = self._chamar(self.stub.PlaylistsComMusica, pb.Id(id=musica_id))
        return [_playlist(p) for p in resposta.playlists]

    # ---- usuários ---------------------------------------------------------
    def obter_usuario(self, id):
        return _usuario(self._chamar(self.stub.ObterUsuario, pb.Id(id=id)))

    def criar_usuario(self, nome, idade, email):
        return _usuario(self._chamar(self.stub.CriarUsuario,
                                     pb.NovoUsuario(nome=nome, idade=idade, email=email)))

    def atualizar_usuario(self, id, nome, idade, email):
        return _usuario(self._chamar(self.stub.AtualizarUsuario,
                                     pb.Usuario(id=id, nome=nome, idade=idade, email=email)))

    def remover_usuario(self, id):
        self._chamar(self.stub.RemoverUsuario, pb.Id(id=id))

    # ---- músicas ----------------------------------------------------------
    def obter_musica(self, id):
        return _musica(self._chamar(self.stub.ObterMusica, pb.Id(id=id)))

    def criar_musica(self, nome, artista, genero, duracao_s):
        return _musica(self._chamar(self.stub.CriarMusica, pb.NovaMusica(
            nome=nome, artista=artista, genero=genero, duracao_s=duracao_s)))

    def atualizar_musica(self, id, nome, artista, genero, duracao_s):
        return _musica(self._chamar(self.stub.AtualizarMusica, pb.Musica(
            id=id, nome=nome, artista=artista, genero=genero, duracao_s=duracao_s)))

    def remover_musica(self, id):
        self._chamar(self.stub.RemoverMusica, pb.Id(id=id))

    # ---- playlists --------------------------------------------------------
    def listar_playlists(self):
        resposta = self._chamar(self.stub.ListarPlaylists, pb.Vazio())
        return [_playlist(p) for p in resposta.playlists]

    def obter_playlist(self, id):
        return _playlist(self._chamar(self.stub.ObterPlaylist, pb.Id(id=id)))

    def criar_playlist(self, nome, descricao, usuario_id, musicas_ids):
        return _playlist(self._chamar(self.stub.CriarPlaylist, pb.NovaPlaylist(
            nome=nome, descricao=descricao, usuario_id=usuario_id, musicas_ids=musicas_ids)))

    def atualizar_playlist(self, id, nome, descricao, musicas_ids):
        return _playlist(self._chamar(self.stub.AtualizarPlaylist, pb.AlteraPlaylist(
            id=id, nome=nome, descricao=descricao, musicas_ids=musicas_ids)))

    def remover_playlist(self, id):
        self._chamar(self.stub.RemoverPlaylist, pb.Id(id=id))


if __name__ == "__main__":
    from python_api.comum.demonstracao import demonstrar
    demonstrar(ClienteGrpc(), "gRPC")
