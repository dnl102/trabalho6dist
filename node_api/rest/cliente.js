/**
 * Cliente REST em Node.js: usa o fetch nativo para falar com a API REST
 * (funciona tanto contra o servidor Node.js na porta 8101 quanto contra o Python na 8001).
 *
 * Executar: node node_api/rest/cliente.js [url]
 */

const { NaoEncontrado, DadosInvalidos } = require("../comum/dados");

const URL_PADRAO = "http://127.0.0.1:8101";

class ClienteRest {
  constructor(url = URL_PADRAO) {
    this.url = url;
  }

  async _chamar(metodo, caminho, corpo = undefined) {
    const opcoes = { method: metodo, headers: {} };
    if (corpo !== undefined) {
      opcoes.headers["Content-Type"] = "application/json";
      opcoes.body = JSON.stringify(corpo);
    }
    const resp = await fetch(this.url + caminho, opcoes);
    if (resp.status === 204) return null;

    const texto = await resp.text();
    let dados = null;
    try {
      dados = texto ? JSON.parse(texto) : null;
    } catch {
      dados = null;
    }

    if (resp.status === 404) throw new NaoEncontrado(dados?.erro || texto);
    if (resp.status === 422) throw new DadosInvalidos(dados?.erro || texto);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${texto}`);
    return dados;
  }

  // ---- as 5 consultas do enunciado ----------------------------------------
  listarUsuarios() { return this._chamar("GET", "/usuarios"); }
  listarMusicas() { return this._chamar("GET", "/musicas"); }
  playlistsDoUsuario(id) { return this._chamar("GET", `/usuarios/${id}/playlists`); }
  musicasDaPlaylist(id) { return this._chamar("GET", `/playlists/${id}/musicas`); }
  playlistsComMusica(id) { return this._chamar("GET", `/musicas/${id}/playlists`); }

  // ---- usuários -----------------------------------------------------------
  obterUsuario(id) { return this._chamar("GET", `/usuarios/${id}`); }
  criarUsuario(nome, idade, email) { return this._chamar("POST", "/usuarios", { nome, idade, email }); }
  atualizarUsuario(id, nome, idade, email) { return this._chamar("PUT", `/usuarios/${id}`, { nome, idade, email }); }
  removerUsuario(id) { return this._chamar("DELETE", `/usuarios/${id}`); }

  // ---- músicas ------------------------------------------------------------
  obterMusica(id) { return this._chamar("GET", `/musicas/${id}`); }
  criarMusica(nome, artista, genero, duracao_s) {
    return this._chamar("POST", "/musicas", { nome, artista, genero, duracao_s });
  }
  atualizarMusica(id, nome, artista, genero, duracao_s) {
    return this._chamar("PUT", `/musicas/${id}`, { nome, artista, genero, duracao_s });
  }
  removerMusica(id) { return this._chamar("DELETE", `/musicas/${id}`); }

  // ---- playlists ----------------------------------------------------------
  listarPlaylists() { return this._chamar("GET", "/playlists"); }
  obterPlaylist(id) { return this._chamar("GET", `/playlists/${id}`); }
  criarPlaylist(nome, descricao, usuario_id, musicas_ids) {
    return this._chamar("POST", "/playlists", { nome, descricao, usuario_id, musicas_ids });
  }
  atualizarPlaylist(id, nome, descricao, musicas_ids) {
    return this._chamar("PUT", `/playlists/${id}`, { nome, descricao, musicas_ids });
  }
  removerPlaylist(id) { return this._chamar("DELETE", `/playlists/${id}`); }
}

if (require.main === module) {
  const { demonstrar } = require("../comum/demonstracao");
  demonstrar(new ClienteRest(process.argv[2] || URL_PADRAO), "REST");
}

module.exports = { ClienteRest };
