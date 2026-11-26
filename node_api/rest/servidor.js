/**
 * Servidor REST em Node.js (Express).
 *
 * Mesma ideia e mesmas rotas do servidor Python (FastAPI), rodando na porta 8101.
 * Executar: node node_api/rest/servidor.js
 */

const express = require("express");
const { NaoEncontrado, DadosInvalidos, criarRepositorioPopulado } = require("../comum/dados");

const PORTA = Number(process.env.PORTA || 8101);
const app = express();
app.use(express.json());

const repo = criarRepositorioPopulado();

// ---- /usuarios ------------------------------------------------------------

app.get("/usuarios", (_, res) => res.json(repo.listarUsuarios()));

app.post("/usuarios", (req, res) => {
  const { nome, idade, email } = req.body || {};
  res.status(201).json(repo.criarUsuario(nome, idade, email));
});

app.get("/usuarios/:id", (req, res) => res.json(repo.obterUsuario(req.params.id)));

app.put("/usuarios/:id", (req, res) => {
  const { nome, idade, email } = req.body || {};
  res.json(repo.atualizarUsuario(req.params.id, nome, idade, email));
});

app.delete("/usuarios/:id", (req, res) => {
  repo.removerUsuario(req.params.id);
  res.status(204).end();
});

app.get("/usuarios/:id/playlists", (req, res) => res.json(repo.playlistsDoUsuario(req.params.id)));

// ---- /musicas -------------------------------------------------------------

app.get("/musicas", (_, res) => res.json(repo.listarMusicas()));

app.post("/musicas", (req, res) => {
  const { nome, artista, genero, duracao_s } = req.body || {};
  res.status(201).json(repo.criarMusica(nome, artista, genero, duracao_s));
});

app.get("/musicas/:id", (req, res) => res.json(repo.obterMusica(req.params.id)));

app.put("/musicas/:id", (req, res) => {
  const { nome, artista, genero, duracao_s } = req.body || {};
  res.json(repo.atualizarMusica(req.params.id, nome, artista, genero, duracao_s));
});

app.delete("/musicas/:id", (req, res) => {
  repo.removerMusica(req.params.id);
  res.status(204).end();
});

app.get("/musicas/:id/playlists", (req, res) => res.json(repo.playlistsComMusica(req.params.id)));

// ---- /playlists -----------------------------------------------------------

app.get("/playlists", (_, res) => res.json(repo.listarPlaylists()));

app.post("/playlists", (req, res) => {
  const { nome, descricao, usuario_id, musicas_ids } = req.body || {};
  res.status(201).json(repo.criarPlaylist(nome, descricao, usuario_id, musicas_ids));
});

app.get("/playlists/:id", (req, res) => res.json(repo.obterPlaylist(req.params.id)));

app.put("/playlists/:id", (req, res) => {
  const { nome, descricao, musicas_ids } = req.body || {};
  res.json(repo.atualizarPlaylist(req.params.id, nome, descricao, musicas_ids));
});

app.delete("/playlists/:id", (req, res) => {
  repo.removerPlaylist(req.params.id);
  res.status(204).end();
});

app.get("/playlists/:id/musicas", (req, res) => res.json(repo.musicasDaPlaylist(req.params.id)));

// ---- tratamento centralizado de erros ------------------------------------

app.use((erro, _req, res, _next) => {
  if (erro instanceof NaoEncontrado) return res.status(404).json({ erro: erro.message });
  if (erro instanceof DadosInvalidos) return res.status(422).json({ erro: erro.message });
  if (erro.type === "entity.parse.failed" || erro.status === 400) {
    return res.status(422).json({ erro: "JSON inválido no corpo da requisição" });
  }
  return res.status(500).json({ erro: "Erro interno do servidor" });
});

app.listen(PORTA, "127.0.0.1", () => {
  console.log(`Servidor REST (Node.js) ouvindo na porta ${PORTA}`);
});
