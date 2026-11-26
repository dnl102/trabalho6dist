/**
 * Cliente GraphQL em Node.js: envia queries/mutations via POST para /graphql.
 * Funciona tanto contra o servidor Node.js (8102) quanto contra o Python (8002).
 *
 * Executar: node node_api/graphql/cliente.js [url]
 */

const { NaoEncontrado, DadosInvalidos } = require("../comum/dados");

const URL_PADRAO = "http://127.0.0.1:8102/graphql";

const USUARIO = "id nome idade email";
const MUSICA = "id nome artista genero duracaoS";
const PLAYLIST = "id nome descricao usuario { id } musicas { id }";

const normalizarMusica = (m) => ({
  id: m.id, nome: m.nome, artista: m.artista, genero: m.genero, duracao_s: m.duracaoS,
});

const normalizarPlaylist = (p) => ({
  id: p.id, nome: p.nome, descricao: p.descricao,
  usuario_id: p.usuario.id, musicas_ids: p.musicas.map((m) => m.id),
});

class ClienteGraphQL {
  constructor(url = URL_PADRAO) {
    this.url = url;
  }

  async _executar(query, variables = {}) {
    const resp = await fetch(this.url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, variables }),
    });
    const corpo = await resp.json();
    if (corpo.errors?.length) {
      const erro = corpo.errors[0];
      const codigo = erro.extensions?.codigo;
      if (codigo === "NAO_ENCONTRADO") throw new NaoEncontrado(erro.message);
      if (codigo === "DADOS_INVALIDOS" || resp.status === 400) throw new DadosInvalidos(erro.message);
      throw new Error(erro.message);
    }
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return corpo.data;
  }

  // ---- as 5 consultas do enunciado ----------------------------------------
  async listarUsuarios() {
    return (await this._executar(`{ usuarios { ${USUARIO} } }`)).usuarios;
  }
  async listarMusicas() {
    return (await this._executar(`{ musicas { ${MUSICA} } }`)).musicas.map(normalizarMusica);
  }
  async playlistsDoUsuario(id) {
    const d = await this._executar(`query($id: Int!) { usuario(id: $id) { playlists { ${PLAYLIST} } } }`, { id });
    return d.usuario.playlists.map(normalizarPlaylist);
  }
  async musicasDaPlaylist(id) {
    const d = await this._executar(`query($id: Int!) { playlist(id: $id) { musicas { ${MUSICA} } } }`, { id });
    return d.playlist.musicas.map(normalizarMusica);
  }
  async playlistsComMusica(id) {
    const d = await this._executar(`query($id: Int!) { musica(id: $id) { playlists { ${PLAYLIST} } } }`, { id });
    return d.musica.playlists.map(normalizarPlaylist);
  }

  // ---- usuários -----------------------------------------------------------
  async obterUsuario(id) {
    return (await this._executar(`query($id: Int!) { usuario(id: $id) { ${USUARIO} } }`, { id })).usuario;
  }
  async criarUsuario(nome, idade, email) {
    const d = await this._executar(
      `mutation($nome: String!, $idade: Int!, $email: String!) {
         criarUsuario(nome: $nome, idade: $idade, email: $email) { ${USUARIO} }
       }`,
      { nome, idade, email },
    );
    return d.criarUsuario;
  }
  async atualizarUsuario(id, nome, idade, email) {
    const d = await this._executar(
      `mutation($id: Int!, $nome: String!, $idade: Int!, $email: String!) {
         atualizarUsuario(id: $id, nome: $nome, idade: $idade, email: $email) { ${USUARIO} }
       }`,
      { id, nome, idade, email },
    );
    return d.atualizarUsuario;
  }
  async removerUsuario(id) {
    await this._executar("mutation($id: Int!) { removerUsuario(id: $id) }", { id });
  }

  // ---- músicas ------------------------------------------------------------
  async obterMusica(id) {
    return normalizarMusica((await this._executar(`query($id: Int!) { musica(id: $id) { ${MUSICA} } }`, { id })).musica);
  }
  async criarMusica(nome, artista, genero, duracao_s) {
    const d = await this._executar(
      `mutation($nome: String!, $artista: String!, $genero: String!, $duracaoS: Int!) {
         criarMusica(nome: $nome, artista: $artista, genero: $genero, duracaoS: $duracaoS) { ${MUSICA} }
       }`,
      { nome, artista, genero, duracaoS: duracao_s },
    );
    return normalizarMusica(d.criarMusica);
  }
  async atualizarMusica(id, nome, artista, genero, duracao_s) {
    const d = await this._executar(
      `mutation($id: Int!, $nome: String!, $artista: String!, $genero: String!, $duracaoS: Int!) {
         atualizarMusica(id: $id, nome: $nome, artista: $artista, genero: $genero, duracaoS: $duracaoS) { ${MUSICA} }
       }`,
      { id, nome, artista, genero, duracaoS: duracao_s },
    );
    return normalizarMusica(d.atualizarMusica);
  }
  async removerMusica(id) {
    await this._executar("mutation($id: Int!) { removerMusica(id: $id) }", { id });
  }

  // ---- playlists ----------------------------------------------------------
  async listarPlaylists() {
    return (await this._executar(`{ playlists { ${PLAYLIST} } }`)).playlists.map(normalizarPlaylist);
  }
  async obterPlaylist(id) {
    return normalizarPlaylist((await this._executar(`query($id: Int!) { playlist(id: $id) { ${PLAYLIST} } }`, { id })).playlist);
  }
  async criarPlaylist(nome, descricao, usuario_id, musicas_ids) {
    const d = await this._executar(
      `mutation($nome: String!, $descricao: String!, $usuarioId: Int!, $musicasIds: [Int!]!) {
         criarPlaylist(nome: $nome, descricao: $descricao, usuarioId: $usuarioId, musicasIds: $musicasIds) { ${PLAYLIST} }
       }`,
      { nome, descricao, usuarioId: usuario_id, musicasIds: musicas_ids },
    );
    return normalizarPlaylist(d.criarPlaylist);
  }
  async atualizarPlaylist(id, nome, descricao, musicas_ids) {
    const d = await this._executar(
      `mutation($id: Int!, $nome: String!, $descricao: String!, $musicasIds: [Int!]!) {
         atualizarPlaylist(id: $id, nome: $nome, descricao: $descricao, musicasIds: $musicasIds) { ${PLAYLIST} }
       }`,
      { id, nome, descricao, musicasIds: musicas_ids },
    );
    return normalizarPlaylist(d.atualizarPlaylist);
  }
  async removerPlaylist(id) {
    await this._executar("mutation($id: Int!) { removerPlaylist(id: $id) }", { id });
  }
}

if (require.main === module) {
  const { demonstrar } = require("../comum/demonstracao");
  demonstrar(new ClienteGraphQL(process.argv[2] || URL_PADRAO), "GraphQL");
}

module.exports = { ClienteGraphQL };
