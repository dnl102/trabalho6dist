/**
 * Servidor gRPC em Node.js (@grpc/grpc-js + @grpc/proto-loader).
 *
 * Usa EXATAMENTE o mesmo contrato grpc_api/musica.proto do servidor Python!
 * Isso ilustra na prática a interoperabilidade multilíngue do gRPC.
 *
 * Executar: node node_api/grpc/servidor.js   (porta 50151)
 */

const path = require("path");
const grpc = require("@grpc/grpc-js");
const protoLoader = require("@grpc/proto-loader");
const { NaoEncontrado, DadosInvalidos, criarRepositorioPopulado } = require("../comum/dados");

const PORTA = Number(process.env.PORTA || 50151);
const PROTO = path.resolve(__dirname, "../../python_api/grpc/musica.proto");

const definicao = protoLoader.loadSync(PROTO, {
  keepCase: true,   // mantém snake_case (usuario_id, musicas_ids, duracao_s) igual ao Python
  longs: Number,
  enums: String,
  defaults: true,
  oneofs: true,
});
const { streaming } = grpc.loadPackageDefinition(definicao);

const repo = criarRepositorioPopulado();

function executar(callback, fn) {
  let resultado;
  try {
    resultado = fn();
  } catch (erro) {
    if (erro instanceof NaoEncontrado) {
      return callback({ code: grpc.status.NOT_FOUND, message: erro.message });
    }
    if (erro instanceof DadosInvalidos) {
      return callback({ code: grpc.status.INVALID_ARGUMENT, message: erro.message });
    }
    return callback({ code: grpc.status.INTERNAL, message: erro.message });
  }
  callback(null, resultado);
}

const servico = {
  // Usuários
  ListarUsuarios: (_call, cb) => executar(cb, () => ({ usuarios: repo.listarUsuarios() })),
  ObterUsuario: (call, cb) => executar(cb, () => repo.obterUsuario(call.request.id)),
  CriarUsuario: (call, cb) => executar(cb, () =>
    repo.criarUsuario(call.request.nome, call.request.idade, call.request.email)),
  AtualizarUsuario: (call, cb) => executar(cb, () =>
    repo.atualizarUsuario(call.request.id, call.request.nome, call.request.idade, call.request.email)),
  RemoverUsuario: (call, cb) => executar(cb, () => { repo.removerUsuario(call.request.id); return {}; }),

  // Músicas
  ListarMusicas: (_call, cb) => executar(cb, () => ({ musicas: repo.listarMusicas() })),
  ObterMusica: (call, cb) => executar(cb, () => repo.obterMusica(call.request.id)),
  CriarMusica: (call, cb) => executar(cb, () =>
    repo.criarMusica(call.request.nome, call.request.artista, call.request.genero, call.request.duracao_s)),
  AtualizarMusica: (call, cb) => executar(cb, () =>
    repo.atualizarMusica(
      call.request.id, call.request.nome, call.request.artista, call.request.genero, call.request.duracao_s)),
  RemoverMusica: (call, cb) => executar(cb, () => { repo.removerMusica(call.request.id); return {}; }),

  // Playlists
  ListarPlaylists: (_call, cb) => executar(cb, () => ({ playlists: repo.listarPlaylists() })),
  ObterPlaylist: (call, cb) => executar(cb, () => repo.obterPlaylist(call.request.id)),
  CriarPlaylist: (call, cb) => executar(cb, () =>
    repo.criarPlaylist(call.request.nome, call.request.descricao, call.request.usuario_id, call.request.musicas_ids)),
  AtualizarPlaylist: (call, cb) => executar(cb, () =>
    repo.atualizarPlaylist(call.request.id, call.request.nome, call.request.descricao, call.request.musicas_ids)),
  RemoverPlaylist: (call, cb) => executar(cb, () => { repo.removerPlaylist(call.request.id); return {}; }),

  // Consultas do enunciado
  PlaylistsDoUsuario: (call, cb) => executar(cb, () => ({ playlists: repo.playlistsDoUsuario(call.request.id) })),
  MusicasDaPlaylist: (call, cb) => executar(cb, () => ({ musicas: repo.musicasDaPlaylist(call.request.id) })),
  PlaylistsComMusica: (call, cb) => executar(cb, () => ({ playlists: repo.playlistsComMusica(call.request.id) })),
};

const servidor = new grpc.Server();
servidor.addService(streaming.Streaming.service, servico);
servidor.bindAsync(`127.0.0.1:${PORTA}`, grpc.ServerCredentials.createInsecure(), (erro) => {
  if (erro) throw erro;
  console.log(`Servidor gRPC (Node.js) ouvindo na porta ${PORTA}`);
});
