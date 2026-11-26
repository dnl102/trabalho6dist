// Teste de carga com k6 (https://k6.io) - mesmo roteiro para as 4 tecnologias
// em ambas as linguagens (Python e Node.js).
//
// Variáveis de ambiente:
//   LINGUAGEM  = python | node
//   TECNOLOGIA = rest | graphql | grpc | soap
//   CARGA      = leve | pesada | escrita
//   VUS        = nº de usuários virtuais simultâneos
//   DURACAO    = tempo de teste (ex.: 20s)
//   SAIDA      = arquivo JSON onde o resumo é gravado

import http from "k6/http";
import grpc from "k6/net/grpc";
import { Rate } from "k6/metrics";

const LINGUAGEM = __ENV.LINGUAGEM || "python";
const TECNOLOGIA = __ENV.TECNOLOGIA || "rest";
const CARGA = __ENV.CARGA || "leve";

const PORTAS = {
  python: { rest: 8001, graphql: 8002, grpc: 50051, soap: 8004 },
  node:   { rest: 8101, graphql: 8102, grpc: 50151, soap: 8104 },
}[LINGUAGEM];
if (!PORTAS) throw new Error(`LINGUAGEM inválida: ${LINGUAGEM}`);

export const options = {
  vus: Number(__ENV.VUS || 10),
  duration: __ENV.DURACAO || "20s",
  summaryTrendStats: ["avg", "med", "p(95)", "p(99)", "max"],
};

const erros = new Rate("erros"); // fração de requisições que falharam

// Mesmo volume de dados criado por comum/dados.py e node_api/comum/dados.js
const N_USUARIOS = 100, N_PLAYLISTS = 300, N_MUSICAS = 1000;
const sortear = (max) => 1 + Math.floor(Math.random() * max);

// ------------------------------------------------------------------ REST
const URL_REST = `http://127.0.0.1:${PORTAS.rest}`;
const JSON_HDR = { headers: { "Content-Type": "application/json" } };

const rest = {
  playlistsDoUsuario: (id) => http.get(`${URL_REST}/usuarios/${id}/playlists`).status === 200,
  musicasDaPlaylist: (id) => http.get(`${URL_REST}/playlists/${id}/musicas`).status === 200,
  playlistsComMusica: (id) => http.get(`${URL_REST}/musicas/${id}/playlists`).status === 200,
  listarMusicas: () => http.get(`${URL_REST}/musicas`).status === 200,
  criarUsuario: () => {
    const r = http.post(
      `${URL_REST}/usuarios`,
      JSON.stringify({ nome: "Carga", idade: 30, email: "carga@streaming.com" }),
      JSON_HDR,
    );
    return r.status === 201 ? r.json("id") : null;
  },
  atualizarUsuario: (id) =>
    http.put(
      `${URL_REST}/usuarios/${id}`,
      JSON.stringify({ nome: "Carga 2", idade: 31, email: "carga2@streaming.com" }),
      JSON_HDR,
    ).status === 200,
  removerUsuario: (id) => http.del(`${URL_REST}/usuarios/${id}`).status === 204,
};

// --------------------------------------------------------------- GraphQL
const URL_GRAPHQL = `http://127.0.0.1:${PORTAS.graphql}/graphql`;
const PLAYLIST = "id nome descricao usuario { id } musicas { id }";
const MUSICA = "id nome artista genero duracaoS";

function graphql(query, variables) {
  const r = http.post(URL_GRAPHQL, JSON.stringify({ query, variables }), JSON_HDR);
  const ok = r.status === 200 && !r.body.includes('"errors"');
  return ok ? r : null;
}

const gql = {
  playlistsDoUsuario: (id) =>
    !!graphql(`query($id:Int!){ usuario(id:$id){ playlists { ${PLAYLIST} } } }`, { id }),
  musicasDaPlaylist: (id) =>
    !!graphql(`query($id:Int!){ playlist(id:$id){ musicas { ${MUSICA} } } }`, { id }),
  playlistsComMusica: (id) =>
    !!graphql(`query($id:Int!){ musica(id:$id){ playlists { ${PLAYLIST} } } }`, { id }),
  listarMusicas: () => !!graphql(`{ musicas { ${MUSICA} } }`),
  criarUsuario: () => {
    const r = graphql('mutation { criarUsuario(nome:"Carga", idade:30, email:"carga@streaming.com") { id } }');
    return r ? r.json("data.criarUsuario.id") : null;
  },
  atualizarUsuario: (id) =>
    !!graphql(
      'mutation($id:Int!){ atualizarUsuario(id:$id, nome:"Carga 2", idade:31, email:"carga2@streaming.com") { id } }',
      { id },
    ),
  removerUsuario: (id) => !!graphql("mutation($id:Int!){ removerUsuario(id:$id) }", { id }),
};

// ------------------------------------------------------------------ gRPC
const clienteGrpc = new grpc.Client();
clienteGrpc.load(["../python_api/grpc"], "musica.proto");
let conectado = false;

function rpc(metodo, mensagem) {
  if (!conectado) {
    clienteGrpc.connect(`127.0.0.1:${PORTAS.grpc}`, { plaintext: true });
    conectado = true;
  }
  const r = clienteGrpc.invoke(`streaming.Streaming/${metodo}`, mensagem);
  return r.status === grpc.StatusOK ? r : null;
}

const grpcOps = {
  playlistsDoUsuario: (id) => !!rpc("PlaylistsDoUsuario", { id }),
  musicasDaPlaylist: (id) => !!rpc("MusicasDaPlaylist", { id }),
  playlistsComMusica: (id) => !!rpc("PlaylistsComMusica", { id }),
  listarMusicas: () => !!rpc("ListarMusicas", {}),
  criarUsuario: () => {
    const r = rpc("CriarUsuario", { nome: "Carga", idade: 30, email: "carga@streaming.com" });
    return r ? r.message.id : null;
  },
  atualizarUsuario: (id) =>
    !!rpc("AtualizarUsuario", { id, nome: "Carga 2", idade: 31, email: "carga2@streaming.com" }),
  removerUsuario: (id) => !!rpc("RemoverUsuario", { id }),
};

// ------------------------------------------------------------------ SOAP
const URL_SOAP = `http://127.0.0.1:${PORTAS.soap}/`;
const NS = "http://exemplo.ufc.br/streaming";

function soap(operacao, corpo) {
  const envelope =
    `<?xml version="1.0" encoding="UTF-8"?>` +
    `<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:s="${NS}">` +
    `<soapenv:Body><s:${operacao}>${corpo}</s:${operacao}></soapenv:Body></soapenv:Envelope>`;
  const r = http.post(URL_SOAP, envelope, {
    headers: { "Content-Type": "text/xml; charset=utf-8", SOAPAction: `"${operacao}"` },
  });
  return r.status === 200 && !r.body.includes("Fault>") ? r : null;
}

const soapOps = {
  playlistsDoUsuario: (id) => !!soap("PlaylistsDoUsuario", `<s:id>${id}</s:id>`),
  musicasDaPlaylist: (id) => !!soap("MusicasDaPlaylist", `<s:id>${id}</s:id>`),
  playlistsComMusica: (id) => !!soap("PlaylistsComMusica", `<s:id>${id}</s:id>`),
  listarMusicas: () => !!soap("ListarMusicas", ""),
  criarUsuario: () => {
    const r = soap(
      "CriarUsuario",
      "<s:nome>Carga</s:nome><s:idade>30</s:idade><s:email>carga@streaming.com</s:email>",
    );
    const id = r && r.body.match(/<(?:[a-zA-Z0-9_]+:)?id>(\d+)<\/(?:[a-zA-Z0-9_]+:)?id>/);
    return id ? Number(id[1]) : null;
  },
  atualizarUsuario: (id) =>
    !!soap(
      "AtualizarUsuario",
      `<s:id>${id}</s:id><s:nome>Carga 2</s:nome><s:idade>31</s:idade><s:email>carga2@streaming.com</s:email>`,
    ),
  removerUsuario: (id) => !!soap("RemoverUsuario", `<s:id>${id}</s:id>`),
};

// ------------------------------------------------------------- roteiro
const OPERACOES = { rest, graphql: gql, grpc: grpcOps, soap: soapOps }[TECNOLOGIA];
if (!OPERACOES) throw new Error(`TECNOLOGIA inválida: ${TECNOLOGIA}`);

export default function () {
  if (CARGA === "leve") {
    const sorteio = Math.random();
    if (sorteio < 1 / 3) erros.add(!OPERACOES.playlistsDoUsuario(sortear(N_USUARIOS)));
    else if (sorteio < 2 / 3) erros.add(!OPERACOES.musicasDaPlaylist(sortear(N_PLAYLISTS)));
    else erros.add(!OPERACOES.playlistsComMusica(sortear(N_MUSICAS)));
  } else if (CARGA === "pesada") {
    erros.add(!OPERACOES.listarMusicas());
  } else if (CARGA === "escrita") {
    const id = OPERACOES.criarUsuario();
    erros.add(id === null);
    if (id !== null) {
      erros.add(!OPERACOES.atualizarUsuario(id));
      erros.add(!OPERACOES.removerUsuario(id));
    }
  } else {
    throw new Error(`CARGA inválida: ${CARGA}`);
  }
}

// ------------------------------------------------------- resumo em JSON
export function handleSummary(dados) {
  const m = dados.metrics;
  const duracao = m[TECNOLOGIA === "grpc" ? "grpc_req_duration" : "http_req_duration"].values;
  const requisicoes = m.erros.values.passes + m.erros.values.fails;
  const segundos = dados.state.testRunDurationMs / 1000;
  const resumo = {
    linguagem: LINGUAGEM,
    tecnologia: TECNOLOGIA,
    carga: CARGA,
    vus: options.vus,
    requisicoes,
    requisicoes_por_s: requisicoes / segundos,
    latencia_media_ms: duracao.avg,
    latencia_mediana_ms: duracao.med,
    latencia_p95_ms: duracao["p(95)"],
    latencia_p99_ms: duracao["p(99)"],
    latencia_max_ms: duracao.max,
    taxa_erros: m.erros.values.rate,
    bytes_recebidos_por_req: m.data_received.values.count / requisicoes,
    bytes_enviados_por_req: m.data_sent.values.count / requisicoes,
  };
  return { [__ENV.SAIDA || "resumo.json"]: JSON.stringify(resumo, null, 2) };
}
