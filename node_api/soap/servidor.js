/**
 * Servidor SOAP 1.1 em Node.js (biblioteca "soap" + contrato streaming.wsdl).
 *
 * Mesmo namespace e mesmas 18 operações do servidor Python (Spyne),
 * rodando na porta 8104 (WSDL em http://127.0.0.1:8104/?wsdl).
 *
 * Executar: node node_api/soap/servidor.js
 */

const fs = require("fs");
const http = require("http");
const path = require("path");
const soap = require("soap");
const { NaoEncontrado, DadosInvalidos, criarRepositorioPopulado } = require("../comum/dados");

const PORTA = Number(process.env.PORTA || 8104);
const wsdl = fs.readFileSync(path.join(__dirname, "streaming.wsdl"), "utf8")
  .replace("http://127.0.0.1:8104/", `http://127.0.0.1:${PORTA}/`);
const repo = criarRepositorioPopulado();

function executar(fn) {
  try {
    return fn();
  } catch (erro) {
    if (erro instanceof NaoEncontrado) {
      throw { Fault: { faultcode: "Client.NaoEncontrado", faultstring: erro.message, statusCode: 500 } };
    }
    if (erro instanceof DadosInvalidos) {
      throw { Fault: { faultcode: "Client.DadosInvalidos", faultstring: erro.message, statusCode: 500 } };
    }
    throw { Fault: { faultcode: "Server", faultstring: erro.message, statusCode: 500 } };
  }
}

function extrairIds(musicasIds) {
  if (!musicasIds || musicasIds.integer === undefined) return [];
  const lista = Array.isArray(musicasIds.integer) ? musicasIds.integer : [musicasIds.integer];
  return lista.map(Number);
}

const playlistSoap = (p) => ({
  id: p.id,
  nome: p.nome,
  descricao: p.descricao,
  usuario_id: p.usuario_id,
  musicas_ids: { integer: p.musicas_ids },
});

const servico = {
  StreamingMusicas: {
    StreamingPort: {
      // Usuários
      ListarUsuarios: () => ({ ListarUsuariosResult: { Usuario: repo.listarUsuarios() } }),
      ObterUsuario: (args) => executar(() => ({ ObterUsuarioResult: repo.obterUsuario(args.id) })),
      CriarUsuario: (args) => executar(() => ({
        CriarUsuarioResult: repo.criarUsuario(args.nome, args.idade, args.email),
      })),
      AtualizarUsuario: (args) => executar(() => ({
        AtualizarUsuarioResult: repo.atualizarUsuario(args.id, args.nome, args.idade, args.email),
      })),
      RemoverUsuario: (args) => executar(() => { repo.removerUsuario(args.id); return {}; }),

      // Músicas
      ListarMusicas: () => ({ ListarMusicasResult: { Musica: repo.listarMusicas() } }),
      ObterMusica: (args) => executar(() => ({ ObterMusicaResult: repo.obterMusica(args.id) })),
      CriarMusica: (args) => executar(() => ({
        CriarMusicaResult: repo.criarMusica(args.nome, args.artista, args.genero, args.duracao_s),
      })),
      AtualizarMusica: (args) => executar(() => ({
        AtualizarMusicaResult: repo.atualizarMusica(
          args.id, args.nome, args.artista, args.genero, args.duracao_s),
      })),
      RemoverMusica: (args) => executar(() => { repo.removerMusica(args.id); return {}; }),

      // Playlists
      ListarPlaylists: () => ({
        ListarPlaylistsResult: { Playlist: repo.listarPlaylists().map(playlistSoap) },
      }),
      ObterPlaylist: (args) => executar(() => ({
        ObterPlaylistResult: playlistSoap(repo.obterPlaylist(args.id)),
      })),
      CriarPlaylist: (args) => executar(() => ({
        CriarPlaylistResult: playlistSoap(
          repo.criarPlaylist(args.nome, args.descricao, args.usuario_id, extrairIds(args.musicas_ids))),
      })),
      AtualizarPlaylist: (args) => executar(() => ({
        AtualizarPlaylistResult: playlistSoap(
          repo.atualizarPlaylist(args.id, args.nome, args.descricao, extrairIds(args.musicas_ids))),
      })),
      RemoverPlaylist: (args) => executar(() => { repo.removerPlaylist(args.id); return {}; }),

      // Consultas do enunciado
      PlaylistsDoUsuario: (args) => executar(() => ({
        PlaylistsDoUsuarioResult: { Playlist: repo.playlistsDoUsuario(args.id).map(playlistSoap) },
      })),
      MusicasDaPlaylist: (args) => executar(() => ({
        MusicasDaPlaylistResult: { Musica: repo.musicasDaPlaylist(args.id) },
      })),
      PlaylistsComMusica: (args) => executar(() => ({
        PlaylistsComMusicaResult: { Playlist: repo.playlistsComMusica(args.id).map(playlistSoap) },
      })),
    },
  },
};

const servidor = http.createServer((_req, res) => {
  res.statusCode = 404;
  res.end("Use /?wsdl ou envie uma requisição SOAP POST.");
});

servidor.listen(PORTA, "127.0.0.1", () => {
  soap.listen(servidor, "/", servico, wsdl);
  console.log(`Servidor SOAP (Node.js) ouvindo em http://127.0.0.1:${PORTA}/?wsdl`);
});
