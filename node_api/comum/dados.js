/**
 * Camada de dados compartilhada pelos 4 servidores Node.js (REST, GraphQL, gRPC e SOAP).
 *
 * Espelho exato de comum/dados.py: mesmo modelo, mesmas regras de validação e
 * mesmo gerador determinístico de dados iniciais. Assim, os 8 servidores
 * (4 em Python e 4 em Node.js) respondem exatamente igual.
 */

class NaoEncontrado extends Error {
  constructor(mensagem) {
    super(mensagem);
    this.name = "NaoEncontrado";
  }
}

class DadosInvalidos extends Error {
  constructor(mensagem) {
    super(mensagem);
    this.name = "DadosInvalidos";
  }
}

// Mesmo gerador linear congruente de comum/dados.py (usando BigInt para evitar
// perda de precisão em 53 bits e manter igualdade bit-a-bit com o Python).
class GeradorDeterministico {
  constructor(semente = 42) {
    this.estado = BigInt(semente);
  }

  proximo() {
    this.estado = (this.estado * 1103515245n + 12345n) & 0x7fffffffn;
    return Number(this.estado);
  }

  inteiro(minimo, maximo) {
    return minimo + (this.proximo() % (maximo - minimo + 1));
  }

  escolher(lista) {
    return lista[this.proximo() % lista.length];
  }

  amostra(lista, quantidade) {
    const escolhidos = [];
    const usados = new Set();
    while (escolhidos.length < quantidade) {
      const item = this.escolher(lista);
      if (!usados.has(item)) {
        usados.add(item);
        escolhidos.push(item);
      }
    }
    return escolhidos;
  }
}

class Repositorio {
  constructor() {
    this.usuarios = new Map();
    this.musicas = new Map();
    this.playlists = new Map();
    this._proximoId = { usuario: 1, musica: 1, playlist: 1 };
  }

  _novoId(tipo) {
    const novo = this._proximoId[tipo];
    this._proximoId[tipo] += 1;
    return novo;
  }

  // ---- validações ---------------------------------------------------------

  _inteiro(valor, campo) {
    if (typeof valor === "boolean" || valor === null || valor === undefined || Array.isArray(valor)) {
      throw new DadosInvalidos(`O campo '${campo}' deve ser um número inteiro`);
    }
    if (typeof valor === "string") {
      if (!/^-?\d+$/.test(valor.trim())) {
        throw new DadosInvalidos(`O campo '${campo}' deve ser um número inteiro`);
      }
      return Number(valor.trim());
    }
    if (typeof valor !== "number" || !Number.isInteger(valor)) {
      throw new DadosInvalidos(`O campo '${campo}' deve ser um número inteiro`);
    }
    return valor;
  }

  _validarTexto(valor, campo) {
    if (typeof valor !== "string" || !valor.trim()) {
      throw new DadosInvalidos(`O campo '${campo}' não pode ser vazio`);
    }
  }

  _validarIdade(idade) {
    const n = this._inteiro(idade, "idade");
    if (n < 0) throw new DadosInvalidos("A idade não pode ser negativa");
    return n;
  }

  _validarEmail(email) {
    if (typeof email !== "string" || !email.trim().includes("@")) {
      throw new DadosInvalidos("O campo 'email' deve ser um e-mail válido");
    }
  }

  _validarDuracao(duracaoS) {
    const n = this._inteiro(duracaoS, "duracao_s");
    if (n <= 0) throw new DadosInvalidos("A duração da música deve ser maior que zero");
    return n;
  }

  _validarMusicas(musicasIds) {
    if (!Array.isArray(musicasIds) || musicasIds.length === 0) {
      throw new DadosInvalidos("Uma playlist precisa ter pelo menos 1 música");
    }
    const unicas = [];
    const vistas = new Set();
    for (const rawId of musicasIds) {
      const mid = this._inteiro(rawId, "musicas_ids");
      if (!this.musicas.has(mid)) {
        throw new DadosInvalidos(`Música ${mid} não existe`);
      }
      if (!vistas.has(mid)) {
        vistas.add(mid);
        unicas.push(mid);
      }
    }
    return unicas;
  }

  // ---- usuários -----------------------------------------------------------

  listarUsuarios() {
    return Array.from(this.usuarios.values());
  }

  obterUsuario(id) {
    const uid = this._inteiro(id, "id");
    const usuario = this.usuarios.get(uid);
    if (!usuario) throw new NaoEncontrado(`Usuário ${uid} não encontrado`);
    return usuario;
  }

  criarUsuario(nome, idade, email) {
    this._validarTexto(nome, "nome");
    const idadeVal = this._validarIdade(idade);
    this._validarEmail(email);
    const usuario = { id: this._novoId("usuario"), nome, idade: idadeVal, email };
    this.usuarios.set(usuario.id, usuario);
    return usuario;
  }

  atualizarUsuario(id, nome, idade, email) {
    this._validarTexto(nome, "nome");
    const idadeVal = this._validarIdade(idade);
    this._validarEmail(email);
    const usuario = this.obterUsuario(id);
    usuario.nome = nome;
    usuario.idade = idadeVal;
    usuario.email = email;
    return usuario;
  }

  removerUsuario(id) {
    const uid = this._inteiro(id, "id");
    this.obterUsuario(uid);
    this.usuarios.delete(uid);
    for (const [pid, playlist] of this.playlists.entries()) {
      if (playlist.usuario_id === uid) this.playlists.delete(pid);
    }
  }

  // ---- músicas ------------------------------------------------------------

  listarMusicas() {
    return Array.from(this.musicas.values());
  }

  obterMusica(id) {
    const mid = this._inteiro(id, "id");
    const musica = this.musicas.get(mid);
    if (!musica) throw new NaoEncontrado(`Música ${mid} não encontrada`);
    return musica;
  }

  criarMusica(nome, artista, genero, duracaoS) {
    this._validarTexto(nome, "nome");
    this._validarTexto(artista, "artista");
    this._validarTexto(genero, "genero");
    const duracaoVal = this._validarDuracao(duracaoS);
    const musica = {
      id: this._novoId("musica"),
      nome,
      artista,
      genero,
      duracao_s: duracaoVal,
    };
    this.musicas.set(musica.id, musica);
    return musica;
  }

  atualizarMusica(id, nome, artista, genero, duracaoS) {
    this._validarTexto(nome, "nome");
    this._validarTexto(artista, "artista");
    this._validarTexto(genero, "genero");
    const duracaoVal = this._validarDuracao(duracaoS);
    const musica = this.obterMusica(id);
    musica.nome = nome;
    musica.artista = artista;
    musica.genero = genero;
    musica.duracao_s = duracaoVal;
    return musica;
  }

  removerMusica(id) {
    const mid = this._inteiro(id, "id");
    this.obterMusica(mid);
    this.musicas.delete(mid);
    for (const [pid, playlist] of this.playlists.entries()) {
      if (playlist.musicas_ids.includes(mid)) {
        playlist.musicas_ids = playlist.musicas_ids.filter((m) => m !== mid);
        if (playlist.musicas_ids.length === 0) this.playlists.delete(pid);
      }
    }
  }

  // ---- playlists ----------------------------------------------------------

  listarPlaylists() {
    return Array.from(this.playlists.values());
  }

  obterPlaylist(id) {
    const pid = this._inteiro(id, "id");
    const playlist = this.playlists.get(pid);
    if (!playlist) throw new NaoEncontrado(`Playlist ${pid} não encontrada`);
    return playlist;
  }

  criarPlaylist(nome, descricao, usuarioId, musicasIds) {
    this._validarTexto(nome, "nome");
    this._validarTexto(descricao, "descricao");
    const uid = this._inteiro(usuarioId, "usuario_id");
    if (!this.usuarios.has(uid)) {
      throw new DadosInvalidos(`Usuário ${uid} não existe`);
    }
    const ids = this._validarMusicas(musicasIds);
    const playlist = {
      id: this._novoId("playlist"),
      nome,
      descricao,
      usuario_id: uid,
      musicas_ids: ids,
    };
    this.playlists.set(playlist.id, playlist);
    return playlist;
  }

  atualizarPlaylist(id, nome, descricao, musicasIds) {
    this._validarTexto(nome, "nome");
    this._validarTexto(descricao, "descricao");
    const playlist = this.obterPlaylist(id);
    playlist.musicas_ids = this._validarMusicas(musicasIds);
    playlist.nome = nome;
    playlist.descricao = descricao;
    return playlist;
  }

  removerPlaylist(id) {
    const pid = this._inteiro(id, "id");
    this.obterPlaylist(pid);
    this.playlists.delete(pid);
  }

  // ---- consultas pedidas no enunciado -------------------------------------

  playlistsDoUsuario(usuarioId) {
    const uid = this._inteiro(usuarioId, "id");
    this.obterUsuario(uid);
    return Array.from(this.playlists.values()).filter((p) => p.usuario_id === uid);
  }

  musicasDaPlaylist(playlistId) {
    const playlist = this.obterPlaylist(playlistId);
    return playlist.musicas_ids.map((mid) => this.musicas.get(mid));
  }

  playlistsComMusica(musicaId) {
    const mid = this._inteiro(musicaId, "id");
    this.obterMusica(mid);
    return Array.from(this.playlists.values()).filter((p) => p.musicas_ids.includes(mid));
  }

  // ---- dados iniciais (idênticos ao Python) -------------------------------

  popular(nUsuarios = 100, nMusicas = 1000, playlistsPorUsuario = 3, musicasPorPlaylist = 10, semente = 42) {
    const rng = new GeradorDeterministico(semente);
    const nomes = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Felipe", "Gabi", "Hugo"];
    const artistas = [
      "Djavan", "Elis Regina", "Gilberto Gil", "Marisa Monte",
      "Caetano Veloso", "Rita Lee", "Tim Maia", "Gal Costa",
    ];
    const generos = ["MPB", "Samba", "Bossa Nova", "Rock", "Pop", "Forró"];

    for (let i = 1; i <= nUsuarios; i++) {
      const nome = `${rng.escolher(nomes)} ${i}`;
      const idade = rng.inteiro(14, 80);
      this.criarUsuario(nome, idade, `usuario${i}@streaming.com`);
    }

    for (let i = 1; i <= nMusicas; i++) {
      this.criarMusica(
        `Música ${i}`,
        rng.escolher(artistas),
        rng.escolher(generos),
        rng.inteiro(120, 360),
      );
    }

    const idsMusicas = Array.from(this.musicas.keys());
    for (const usuarioId of this.usuarios.keys()) {
      for (let j = 1; j <= playlistsPorUsuario; j++) {
        const escolhidas = rng.amostra(idsMusicas, musicasPorPlaylist);
        this.criarPlaylist(
          `Playlist ${j} do usuário ${usuarioId}`,
          `Seleção ${j} para ouvir no dia a dia`,
          usuarioId,
          escolhidas,
        );
      }
    }
  }
}

function criarRepositorioPopulado() {
  const repo = new Repositorio();
  repo.popular();
  return repo;
}

module.exports = { Repositorio, NaoEncontrado, DadosInvalidos, criarRepositorioPopulado };
