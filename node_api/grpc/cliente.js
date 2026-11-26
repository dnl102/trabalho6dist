/**
 * Cliente gRPC em Node.js: carrega grpc_api/musica.proto e chama o servidor
 * via HTTP/2 + Protocol Buffers (funciona contra Node.js na 50151 ou Python na 50051).
 *
 * Executar: node node_api/grpc/cliente.js [host:porta]
 */

const path = require("path");
const grpc = require("@grpc/grpc-js");
const protoLoader = require("@grpc/proto-loader");
const { NaoEncontrado, DadosInvalidos } = require("../comum/dados");

const ENDERECO_PADRAO = "127.0.0.1:50151";
const PROTO = path.resolve(__dirname, "../../python_api/grpc/musica.proto");

const definicao = protoLoader.loadSync(PROTO, {
  keepCase: true,
  longs: Number,
  enums: String,
  defaults: true,
  oneofs: true,
});
const { streaming } = grpc.loadPackageDefinition(definicao);

class ClienteGrpc {
  constructor(endereco = ENDERECO_PADRAO) {
    this.stub = new streaming.Streaming(endereco, grpc.credentials.createInsecure());
  }

  _chamar(metodo, req = {}) {
    return new Promise((resolve, reject) => {
      this.stub[metodo](req, (erro, resposta) => {
        if (!erro) return resolve(resposta);
        if (erro.code === grpc.status.NOT_FOUND) return reject(new NaoEncontrado(erro.details));
        if (erro.code === grpc.status.INVALID_ARGUMENT) return reject(new DadosInvalidos(erro.details));
        return reject(erro);
      });
    });
  }

  fechar() {
    this.stub.close();
  }

  // ---- as 5 consultas do enunciado ----------------------------------------
  async listarUsuarios() { return (await this._chamar("ListarUsuarios")).usuarios; }
  async listarMusicas() { return (await this._chamar("ListarMusicas")).musicas; }
  async playlistsDoUsuario(id) { return (await this._chamar("PlaylistsDoUsuario", { id })).playlists; }
  async musicasDaPlaylist(id) { return (await this._chamar("MusicasDaPlaylist", { id })).musicas; }
  async playlistsComMusica(id) { return (await this._chamar("PlaylistsComMusica", { id })).playlists; }

  // ---- usuários -----------------------------------------------------------
  obterUsuario(id) { return this._chamar("ObterUsuario", { id }); }
  criarUsuario(nome, idade, email) { return this._chamar("CriarUsuario", { nome, idade, email }); }
  atualizarUsuario(id, nome, idade, email) { return this._chamar("AtualizarUsuario", { id, nome, idade, email }); }
  removerUsuario(id) { return this._chamar("RemoverUsuario", { id }); }

  // ---- músicas ------------------------------------------------------------
  obterMusica(id) { return this._chamar("ObterMusica", { id }); }
  criarMusica(nome, artista, genero, duracao_s) {
    return this._chamar("CriarMusica", { nome, artista, genero, duracao_s });
  }
  atualizarMusica(id, nome, artista, genero, duracao_s) {
    return this._chamar("AtualizarMusica", { id, nome, artista, genero, duracao_s });
  }
  removerMusica(id) { return this._chamar("RemoverMusica", { id }); }

  // ---- playlists ----------------------------------------------------------
  async listarPlaylists() { return (await this._chamar("ListarPlaylists")).playlists; }
  obterPlaylist(id) { return this._chamar("ObterPlaylist", { id }); }
  criarPlaylist(nome, descricao, usuario_id, musicas_ids) {
    return this._chamar("CriarPlaylist", { nome, descricao, usuario_id, musicas_ids });
  }
  atualizarPlaylist(id, nome, descricao, musicas_ids) {
    return this._chamar("AtualizarPlaylist", { id, nome, descricao, musicas_ids });
  }
  removerPlaylist(id) { return this._chamar("RemoverPlaylist", { id }); }
}

if (require.main === module) {
  const { demonstrar } = require("../comum/demonstracao");
  const cliente = new ClienteGrpc(process.argv[2] || ENDERECO_PADRAO);
  demonstrar(cliente, "gRPC").finally(() => cliente.fechar());
}

module.exports = { ClienteGrpc };
