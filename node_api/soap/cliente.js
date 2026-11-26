/**
 * Cliente SOAP em Node.js: lê o WSDL do servidor e cria os métodos automaticamente
 * (funciona contra o servidor Node.js na 8104 ou o Python na 8004).
 *
 * Executar: node node_api/soap/cliente.js [url_wsdl]
 */

const soap = require("soap");
const { NaoEncontrado, DadosInvalidos } = require("../comum/dados");

const WSDL_PADRAO = "http://127.0.0.1:8104/?wsdl";

const normalizarUsuario = (u) => ({
  id: Number(u.id), nome: u.nome, idade: Number(u.idade), email: u.email,
});

const normalizarMusica = (m) => ({
  id: Number(m.id), nome: m.nome, artista: m.artista, genero: m.genero, duracao_s: Number(m.duracao_s),
});

const normalizarPlaylist = (p) => {
  const bruto = p.musicas_ids?.integer;
  const ids = bruto === undefined ? [] : (Array.isArray(bruto) ? bruto : [bruto]).map(Number);
  return {
    id: Number(p.id), nome: p.nome, descricao: p.descricao,
    usuario_id: Number(p.usuario_id), musicas_ids: ids,
  };
};

const comoLista = (valor) => (valor === undefined || valor === null ? [] : Array.isArray(valor) ? valor : [valor]);

class ClienteSoap {
  constructor(wsdl = WSDL_PADRAO) {
    this.wsdl = wsdl;
    this._clientePromise = null;
  }

  _cliente() {
    if (!this._clientePromise) this._clientePromise = soap.createClientAsync(this.wsdl);
    return this._clientePromise;
  }

  async _chamar(operacao, args = {}) {
    const cliente = await this._cliente();
    try {
      const [resultado] = await cliente[`${operacao}Async`](args);
      return resultado;
    } catch (erro) {
      const fault = erro.root?.Envelope?.Body?.Fault;
      if (fault) {
        const codigo = String(fault.faultcode || "").split(":").pop();
        const msg = fault.faultstring || erro.message;
        if (codigo.endsWith("NaoEncontrado")) throw new NaoEncontrado(msg);
        if (codigo.endsWith("DadosInvalidos") || codigo.startsWith("Client.") || codigo === "Client") {
          throw new DadosInvalidos(msg);
        }
      }
      throw erro;
    }
  }

  // ---- as 5 consultas do enunciado ----------------------------------------
  async listarUsuarios() {
    const r = await this._chamar("ListarUsuarios");
    return comoLista(r?.ListarUsuariosResult?.Usuario).map(normalizarUsuario);
  }
  async listarMusicas() {
    const r = await this._chamar("ListarMusicas");
    return comoLista(r?.ListarMusicasResult?.Musica).map(normalizarMusica);
  }
  async playlistsDoUsuario(id) {
    const r = await this._chamar("PlaylistsDoUsuario", { id });
    return comoLista(r?.PlaylistsDoUsuarioResult?.Playlist).map(normalizarPlaylist);
  }
  async musicasDaPlaylist(id) {
    const r = await this._chamar("MusicasDaPlaylist", { id });
    return comoLista(r?.MusicasDaPlaylistResult?.Musica).map(normalizarMusica);
  }
  async playlistsComMusica(id) {
    const r = await this._chamar("PlaylistsComMusica", { id });
    return comoLista(r?.PlaylistsComMusicaResult?.Playlist).map(normalizarPlaylist);
  }

  // ---- usuários -----------------------------------------------------------
  async obterUsuario(id) {
    return normalizarUsuario((await this._chamar("ObterUsuario", { id })).ObterUsuarioResult);
  }
  async criarUsuario(nome, idade, email) {
    return normalizarUsuario((await this._chamar("CriarUsuario", { nome, idade, email })).CriarUsuarioResult);
  }
  async atualizarUsuario(id, nome, idade, email) {
    return normalizarUsuario((await this._chamar("AtualizarUsuario", { id, nome, idade, email })).AtualizarUsuarioResult);
  }
  async removerUsuario(id) { await this._chamar("RemoverUsuario", { id }); }

  // ---- músicas ------------------------------------------------------------
  async obterMusica(id) {
    return normalizarMusica((await this._chamar("ObterMusica", { id })).ObterMusicaResult);
  }
  async criarMusica(nome, artista, genero, duracao_s) {
    return normalizarMusica((await this._chamar("CriarMusica", { nome, artista, genero, duracao_s })).CriarMusicaResult);
  }
  async atualizarMusica(id, nome, artista, genero, duracao_s) {
    return normalizarMusica(
      (await this._chamar("AtualizarMusica", { id, nome, artista, genero, duracao_s })).AtualizarMusicaResult);
  }
  async removerMusica(id) { await this._chamar("RemoverMusica", { id }); }

  // ---- playlists ----------------------------------------------------------
  async listarPlaylists() {
    const r = await this._chamar("ListarPlaylists");
    return comoLista(r?.ListarPlaylistsResult?.Playlist).map(normalizarPlaylist);
  }
  async obterPlaylist(id) {
    return normalizarPlaylist((await this._chamar("ObterPlaylist", { id })).ObterPlaylistResult);
  }
  async criarPlaylist(nome, descricao, usuario_id, musicas_ids) {
    const r = await this._chamar("CriarPlaylist", { nome, descricao, usuario_id, musicas_ids: { integer: musicas_ids } });
    return normalizarPlaylist(r.CriarPlaylistResult);
  }
  async atualizarPlaylist(id, nome, descricao, musicas_ids) {
    const r = await this._chamar("AtualizarPlaylist", { id, nome, descricao, musicas_ids: { integer: musicas_ids } });
    return normalizarPlaylist(r.AtualizarPlaylistResult);
  }
  async removerPlaylist(id) { await this._chamar("RemoverPlaylist", { id }); }
}

if (require.main === module) {
  const { demonstrar } = require("../comum/demonstracao");
  demonstrar(new ClienteSoap(process.argv[2] || WSDL_PADRAO), "SOAP");
}

module.exports = { ClienteSoap };
