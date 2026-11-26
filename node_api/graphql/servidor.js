/**
 * Servidor GraphQL em Node.js (graphql + graphql-http).
 *
 * Mesmo esquema e mesmas operações do servidor Python (Strawberry),
 * rodando na porta 8102 em /graphql.
 * Executar: node node_api/graphql/servidor.js
 */

const http = require("http");
const {
  GraphQLSchema,
  GraphQLObjectType,
  GraphQLInt,
  GraphQLString,
  GraphQLBoolean,
  GraphQLList,
  GraphQLNonNull,
  GraphQLError,
} = require("graphql");
const { createHandler } = require("graphql-http/lib/use/http");
const { NaoEncontrado, DadosInvalidos, criarRepositorioPopulado } = require("../comum/dados");

const PORTA = Number(process.env.PORTA || 8102);
const repo = criarRepositorioPopulado();

function traduzirErros(fn) {
  try {
    return fn();
  } catch (erro) {
    if (erro instanceof NaoEncontrado) {
      throw new GraphQLError(erro.message, { extensions: { codigo: "NAO_ENCONTRADO" } });
    }
    if (erro instanceof DadosInvalidos) {
      throw new GraphQLError(erro.message, { extensions: { codigo: "DADOS_INVALIDOS" } });
    }
    throw erro;
  }
}

// ---- tipos do esquema (equivalentes aos @strawberry.type do Python) -------

const UsuarioType = new GraphQLObjectType({
  name: "Usuario",
  fields: () => ({
    id: { type: new GraphQLNonNull(GraphQLInt) },
    nome: { type: new GraphQLNonNull(GraphQLString) },
    idade: { type: new GraphQLNonNull(GraphQLInt) },
    email: { type: new GraphQLNonNull(GraphQLString) },
    playlists: {
      type: new GraphQLNonNull(new GraphQLList(new GraphQLNonNull(PlaylistType))),
      resolve: (u) => repo.playlistsDoUsuario(u.id),
    },
  }),
});

const MusicaType = new GraphQLObjectType({
  name: "Musica",
  fields: () => ({
    id: { type: new GraphQLNonNull(GraphQLInt) },
    nome: { type: new GraphQLNonNull(GraphQLString) },
    artista: { type: new GraphQLNonNull(GraphQLString) },
    genero: { type: new GraphQLNonNull(GraphQLString) },
    duracaoS: {
      type: new GraphQLNonNull(GraphQLInt),
      resolve: (m) => m.duracao_s,
    },
    playlists: {
      type: new GraphQLNonNull(new GraphQLList(new GraphQLNonNull(PlaylistType))),
      resolve: (m) => repo.playlistsComMusica(m.id),
    },
  }),
});

const PlaylistType = new GraphQLObjectType({
  name: "Playlist",
  fields: () => ({
    id: { type: new GraphQLNonNull(GraphQLInt) },
    nome: { type: new GraphQLNonNull(GraphQLString) },
    descricao: { type: new GraphQLNonNull(GraphQLString) },
    usuario: {
      type: new GraphQLNonNull(UsuarioType),
      resolve: (p) => repo.obterUsuario(p.usuario_id),
    },
    musicas: {
      type: new GraphQLNonNull(new GraphQLList(new GraphQLNonNull(MusicaType))),
      resolve: (p) => repo.musicasDaPlaylist(p.id),
    },
  }),
});

// ---- consultas (Query) ----------------------------------------------------

const QueryType = new GraphQLObjectType({
  name: "Query",
  fields: {
    usuarios: {
      type: new GraphQLNonNull(new GraphQLList(new GraphQLNonNull(UsuarioType))),
      resolve: () => repo.listarUsuarios(),
    },
    usuario: {
      type: new GraphQLNonNull(UsuarioType),
      args: { id: { type: new GraphQLNonNull(GraphQLInt) } },
      resolve: (_, { id }) => traduzirErros(() => repo.obterUsuario(id)),
    },
    musicas: {
      type: new GraphQLNonNull(new GraphQLList(new GraphQLNonNull(MusicaType))),
      resolve: () => repo.listarMusicas(),
    },
    musica: {
      type: new GraphQLNonNull(MusicaType),
      args: { id: { type: new GraphQLNonNull(GraphQLInt) } },
      resolve: (_, { id }) => traduzirErros(() => repo.obterMusica(id)),
    },
    playlists: {
      type: new GraphQLNonNull(new GraphQLList(new GraphQLNonNull(PlaylistType))),
      resolve: () => repo.listarPlaylists(),
    },
    playlist: {
      type: new GraphQLNonNull(PlaylistType),
      args: { id: { type: new GraphQLNonNull(GraphQLInt) } },
      resolve: (_, { id }) => traduzirErros(() => repo.obterPlaylist(id)),
    },
  },
});

// ---- alterações (Mutation) ------------------------------------------------

const MutationType = new GraphQLObjectType({
  name: "Mutation",
  fields: {
    criarUsuario: {
      type: new GraphQLNonNull(UsuarioType),
      args: {
        nome: { type: new GraphQLNonNull(GraphQLString) },
        idade: { type: new GraphQLNonNull(GraphQLInt) },
        email: { type: new GraphQLNonNull(GraphQLString) },
      },
      resolve: (_, { nome, idade, email }) => traduzirErros(() => repo.criarUsuario(nome, idade, email)),
    },
    atualizarUsuario: {
      type: new GraphQLNonNull(UsuarioType),
      args: {
        id: { type: new GraphQLNonNull(GraphQLInt) },
        nome: { type: new GraphQLNonNull(GraphQLString) },
        idade: { type: new GraphQLNonNull(GraphQLInt) },
        email: { type: new GraphQLNonNull(GraphQLString) },
      },
      resolve: (_, { id, nome, idade, email }) =>
        traduzirErros(() => repo.atualizarUsuario(id, nome, idade, email)),
    },
    removerUsuario: {
      type: new GraphQLNonNull(GraphQLBoolean),
      args: { id: { type: new GraphQLNonNull(GraphQLInt) } },
      resolve: (_, { id }) => { traduzirErros(() => repo.removerUsuario(id)); return true; },
    },
    criarMusica: {
      type: new GraphQLNonNull(MusicaType),
      args: {
        nome: { type: new GraphQLNonNull(GraphQLString) },
        artista: { type: new GraphQLNonNull(GraphQLString) },
        genero: { type: new GraphQLNonNull(GraphQLString) },
        duracaoS: { type: new GraphQLNonNull(GraphQLInt) },
      },
      resolve: (_, { nome, artista, genero, duracaoS }) =>
        traduzirErros(() => repo.criarMusica(nome, artista, genero, duracaoS)),
    },
    atualizarMusica: {
      type: new GraphQLNonNull(MusicaType),
      args: {
        id: { type: new GraphQLNonNull(GraphQLInt) },
        nome: { type: new GraphQLNonNull(GraphQLString) },
        artista: { type: new GraphQLNonNull(GraphQLString) },
        genero: { type: new GraphQLNonNull(GraphQLString) },
        duracaoS: { type: new GraphQLNonNull(GraphQLInt) },
      },
      resolve: (_, { id, nome, artista, genero, duracaoS }) =>
        traduzirErros(() => repo.atualizarMusica(id, nome, artista, genero, duracaoS)),
    },
    removerMusica: {
      type: new GraphQLNonNull(GraphQLBoolean),
      args: { id: { type: new GraphQLNonNull(GraphQLInt) } },
      resolve: (_, { id }) => { traduzirErros(() => repo.removerMusica(id)); return true; },
    },
    criarPlaylist: {
      type: new GraphQLNonNull(PlaylistType),
      args: {
        nome: { type: new GraphQLNonNull(GraphQLString) },
        descricao: { type: new GraphQLNonNull(GraphQLString) },
        usuarioId: { type: new GraphQLNonNull(GraphQLInt) },
        musicasIds: { type: new GraphQLNonNull(new GraphQLList(new GraphQLNonNull(GraphQLInt))) },
      },
      resolve: (_, { nome, descricao, usuarioId, musicasIds }) =>
        traduzirErros(() => repo.criarPlaylist(nome, descricao, usuarioId, musicasIds)),
    },
    atualizarPlaylist: {
      type: new GraphQLNonNull(PlaylistType),
      args: {
        id: { type: new GraphQLNonNull(GraphQLInt) },
        nome: { type: new GraphQLNonNull(GraphQLString) },
        descricao: { type: new GraphQLNonNull(GraphQLString) },
        musicasIds: { type: new GraphQLNonNull(new GraphQLList(new GraphQLNonNull(GraphQLInt))) },
      },
      resolve: (_, { id, nome, descricao, musicasIds }) =>
        traduzirErros(() => repo.atualizarPlaylist(id, nome, descricao, musicasIds)),
    },
    removerPlaylist: {
      type: new GraphQLNonNull(GraphQLBoolean),
      args: { id: { type: new GraphQLNonNull(GraphQLInt) } },
      resolve: (_, { id }) => { traduzirErros(() => repo.removerPlaylist(id)); return true; },
    },
  },
});

const schema = new GraphQLSchema({ query: QueryType, mutation: MutationType });
const handler = createHandler({ schema });

const servidor = http.createServer((req, res) => {
  const caminho = new URL(req.url, "http://127.0.0.1").pathname;
  if (caminho === "/graphql") return handler(req, res);
  res.writeHead(404).end();
});

servidor.listen(PORTA, "127.0.0.1", () => {
  console.log(`Servidor GraphQL (Node.js) ouvindo em http://127.0.0.1:${PORTA}/graphql`);
});
