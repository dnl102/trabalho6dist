"""
Servidor SOAP (Spyne).

Ideia central do SOAP: o cliente envia um "envelope" XML dizendo qual
operação quer executar e com quais parâmetros; o servidor responde com
outro envelope XML. O contrato do serviço é descrito em WSDL (também XML),
gerado aqui automaticamente pelo Spyne a partir das classes Python.

Executar:  uv run gunicorn -k gthread -w 1 --threads 10 -b :8004 python_api.soap.servidor:app
Contrato WSDL: http://localhost:8004/?wsdl
"""

from spyne import (Application, Array, ComplexModel, Fault, Integer,
                   Mandatory, ServiceBase, Unicode, rpc)
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

from python_api.comum.dados import DadosInvalidos, NaoEncontrado, criar_repositorio_populado

NAMESPACE = "http://exemplo.ufc.br/streaming"
repo = criar_repositorio_populado()


# ---- tipos de dados (viram tipos XML Schema dentro do WSDL) -------------
# O Spyne lê os atributos dos objetos retornados pela camada de dados,
# então não é preciso convertê-los manualmente.

class Usuario(ComplexModel):
    __namespace__ = NAMESPACE
    id = Integer
    nome = Unicode
    idade = Integer
    email = Unicode


class Musica(ComplexModel):
    __namespace__ = NAMESPACE
    id = Integer
    nome = Unicode
    artista = Unicode
    genero = Unicode
    duracao_s = Integer


class Playlist(ComplexModel):
    __namespace__ = NAMESPACE
    id = Integer
    nome = Unicode
    descricao = Unicode
    usuario_id = Integer
    musicas_ids = Array(Integer)


def executar(funcao):
    """Executa a função e transforma erros da camada de dados em SOAP Faults
    (a forma padrão de o SOAP devolver erros)."""
    try:
        return funcao()
    except NaoEncontrado as erro:
        raise Fault(faultcode="Client.NaoEncontrado", faultstring=str(erro))
    except DadosInvalidos as erro:
        raise Fault(faultcode="Client.DadosInvalidos", faultstring=str(erro))


# ---- operações do serviço -----------------------------------------------
# @rpc(tipos dos parâmetros, _returns=tipo do retorno).
# Mandatory(...) = parâmetro obrigatório no XML.

class StreamingService(ServiceBase):

    # Usuários
    @rpc(_returns=Array(Usuario))
    def ListarUsuarios(ctx):
        return repo.listar_usuarios()

    @rpc(Mandatory(Integer), _returns=Usuario)
    def ObterUsuario(ctx, id):
        return executar(lambda: repo.obter_usuario(id))

    @rpc(Mandatory(Unicode), Mandatory(Integer), Mandatory(Unicode), _returns=Usuario)
    def CriarUsuario(ctx, nome, idade, email):
        return executar(lambda: repo.criar_usuario(nome, idade, email))

    @rpc(Mandatory(Integer), Mandatory(Unicode), Mandatory(Integer), Mandatory(Unicode), _returns=Usuario)
    def AtualizarUsuario(ctx, id, nome, idade, email):
        return executar(lambda: repo.atualizar_usuario(id, nome, idade, email))

    @rpc(Mandatory(Integer))
    def RemoverUsuario(ctx, id):
        executar(lambda: repo.remover_usuario(id))

    # Músicas
    @rpc(_returns=Array(Musica))
    def ListarMusicas(ctx):
        return repo.listar_musicas()

    @rpc(Mandatory(Integer), _returns=Musica)
    def ObterMusica(ctx, id):
        return executar(lambda: repo.obter_musica(id))

    @rpc(Mandatory(Unicode), Mandatory(Unicode), Mandatory(Unicode), Mandatory(Integer), _returns=Musica)
    def CriarMusica(ctx, nome, artista, genero, duracao_s):
        return executar(lambda: repo.criar_musica(nome, artista, genero, duracao_s))

    @rpc(Mandatory(Integer), Mandatory(Unicode), Mandatory(Unicode),
         Mandatory(Unicode), Mandatory(Integer), _returns=Musica)
    def AtualizarMusica(ctx, id, nome, artista, genero, duracao_s):
        return executar(lambda: repo.atualizar_musica(id, nome, artista, genero, duracao_s))

    @rpc(Mandatory(Integer))
    def RemoverMusica(ctx, id):
        executar(lambda: repo.remover_musica(id))

    # Playlists
    @rpc(_returns=Array(Playlist))
    def ListarPlaylists(ctx):
        return repo.listar_playlists()

    @rpc(Mandatory(Integer), _returns=Playlist)
    def ObterPlaylist(ctx, id):
        return executar(lambda: repo.obter_playlist(id))

    @rpc(Mandatory(Unicode), Mandatory(Unicode), Mandatory(Integer), Array(Integer), _returns=Playlist)
    def CriarPlaylist(ctx, nome, descricao, usuario_id, musicas_ids):
        return executar(lambda: repo.criar_playlist(
            nome, descricao, usuario_id, list(musicas_ids or [])))

    @rpc(Mandatory(Integer), Mandatory(Unicode), Mandatory(Unicode), Array(Integer), _returns=Playlist)
    def AtualizarPlaylist(ctx, id, nome, descricao, musicas_ids):
        return executar(lambda: repo.atualizar_playlist(
            id, nome, descricao, list(musicas_ids or [])))

    @rpc(Mandatory(Integer))
    def RemoverPlaylist(ctx, id):
        executar(lambda: repo.remover_playlist(id))

    # Consultas do enunciado
    @rpc(Mandatory(Integer), _returns=Array(Playlist))
    def PlaylistsDoUsuario(ctx, id):
        return executar(lambda: repo.playlists_do_usuario(id))

    @rpc(Mandatory(Integer), _returns=Array(Musica))
    def MusicasDaPlaylist(ctx, id):
        return executar(lambda: repo.musicas_da_playlist(id))

    @rpc(Mandatory(Integer), _returns=Array(Playlist))
    def PlaylistsComMusica(ctx, id):
        return executar(lambda: repo.playlists_com_musica(id))


aplicacao = Application(
    [StreamingService],
    tns=NAMESPACE,
    name="StreamingMusicas",
    in_protocol=Soap11(validator="lxml"),  # valida o XML recebido contra o esquema
    out_protocol=Soap11(),
)
app = WsgiApplication(aplicacao)  # aplicação WSGI, servida pelo gunicorn
