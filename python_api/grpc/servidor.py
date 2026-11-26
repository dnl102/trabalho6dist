"""
Servidor gRPC (grpcio).

Ideia central do gRPC: o cliente chama funções do servidor como se fossem
funções locais (RPC = Remote Procedure Call). O contrato fica no arquivo
musica.proto, e as classes musica_pb2 / musica_pb2_grpc são GERADAS a
partir dele (veja gerar_codigo.sh).

Executar:  uv run python -m python_api.grpc.servidor      (porta 50051)
"""

from concurrent import futures

import grpc

from python_api.comum.dados import DadosInvalidos, NaoEncontrado, criar_repositorio_populado
from python_api.grpc import musica_pb2 as pb
from python_api.grpc import musica_pb2_grpc as pb_grpc

PORTA = 50051
repo = criar_repositorio_populado()


# ---- conversão: objetos da camada de dados -> mensagens protobuf --------

def usuario_pb(u):
    return pb.Usuario(id=u.id, nome=u.nome, idade=u.idade, email=u.email)


def musica_pb(m):
    return pb.Musica(id=m.id, nome=m.nome, artista=m.artista,
                     genero=m.genero, duracao_s=m.duracao_s)


def playlist_pb(p):
    return pb.Playlist(id=p.id, nome=p.nome, descricao=p.descricao,
                       usuario_id=p.usuario_id, musicas_ids=p.musicas_ids)


def executar(contexto, funcao):
    """Executa a função e transforma erros da camada de dados em
    códigos de status do gRPC (equivalentes ao 404 / 422 do HTTP)."""
    try:
        return funcao()
    except NaoEncontrado as erro:
        contexto.abort(grpc.StatusCode.NOT_FOUND, str(erro))
    except DadosInvalidos as erro:
        contexto.abort(grpc.StatusCode.INVALID_ARGUMENT, str(erro))


# ---- implementação do serviço definido no .proto ------------------------
# Cada método recebe a mensagem de entrada (req) e devolve a de saída.

class Streaming(pb_grpc.StreamingServicer):

    # Usuários
    def ListarUsuarios(self, req, ctx):
        return pb.ListaUsuarios(usuarios=[usuario_pb(u) for u in repo.listar_usuarios()])

    def ObterUsuario(self, req, ctx):
        return executar(ctx, lambda: usuario_pb(repo.obter_usuario(req.id)))

    def CriarUsuario(self, req, ctx):
        return executar(ctx, lambda: usuario_pb(
            repo.criar_usuario(req.nome, req.idade, req.email)))

    def AtualizarUsuario(self, req, ctx):
        return executar(ctx, lambda: usuario_pb(
            repo.atualizar_usuario(req.id, req.nome, req.idade, req.email)))

    def RemoverUsuario(self, req, ctx):
        executar(ctx, lambda: repo.remover_usuario(req.id))
        return pb.Vazio()

    # Músicas
    def ListarMusicas(self, req, ctx):
        return pb.ListaMusicas(musicas=[musica_pb(m) for m in repo.listar_musicas()])

    def ObterMusica(self, req, ctx):
        return executar(ctx, lambda: musica_pb(repo.obter_musica(req.id)))

    def CriarMusica(self, req, ctx):
        return executar(ctx, lambda: musica_pb(
            repo.criar_musica(req.nome, req.artista, req.genero, req.duracao_s)))

    def AtualizarMusica(self, req, ctx):
        return executar(ctx, lambda: musica_pb(
            repo.atualizar_musica(req.id, req.nome, req.artista, req.genero, req.duracao_s)))

    def RemoverMusica(self, req, ctx):
        executar(ctx, lambda: repo.remover_musica(req.id))
        return pb.Vazio()

    # Playlists
    def ListarPlaylists(self, req, ctx):
        return pb.ListaPlaylists(playlists=[playlist_pb(p) for p in repo.listar_playlists()])

    def ObterPlaylist(self, req, ctx):
        return executar(ctx, lambda: playlist_pb(repo.obter_playlist(req.id)))

    def CriarPlaylist(self, req, ctx):
        return executar(ctx, lambda: playlist_pb(
            repo.criar_playlist(req.nome, req.descricao, req.usuario_id, list(req.musicas_ids))))

    def AtualizarPlaylist(self, req, ctx):
        return executar(ctx, lambda: playlist_pb(
            repo.atualizar_playlist(req.id, req.nome, req.descricao, list(req.musicas_ids))))

    def RemoverPlaylist(self, req, ctx):
        executar(ctx, lambda: repo.remover_playlist(req.id))
        return pb.Vazio()

    # Consultas do enunciado
    def PlaylistsDoUsuario(self, req, ctx):
        return executar(ctx, lambda: pb.ListaPlaylists(
            playlists=[playlist_pb(p) for p in repo.playlists_do_usuario(req.id)]))

    def MusicasDaPlaylist(self, req, ctx):
        return executar(ctx, lambda: pb.ListaMusicas(
            musicas=[musica_pb(m) for m in repo.musicas_da_playlist(req.id)]))

    def PlaylistsComMusica(self, req, ctx):
        return executar(ctx, lambda: pb.ListaPlaylists(
            playlists=[playlist_pb(p) for p in repo.playlists_com_musica(req.id)]))


def iniciar():
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb_grpc.add_StreamingServicer_to_server(Streaming(), servidor)
    servidor.add_insecure_port(f"[::]:{PORTA}")
    servidor.start()
    print(f"Servidor gRPC ouvindo na porta {PORTA}")
    servidor.wait_for_termination()


if __name__ == "__main__":
    iniciar()
