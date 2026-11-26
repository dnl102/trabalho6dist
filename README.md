<img src="assets/icon.svg" width="64" height="64" alt="">

# Trabalho 6 — Comparação de Tecnologias de Invocação de Serviços Remotos

Computação Distribuída · Prof. Nabor C. Mendonça

O mesmo **serviço de streaming de músicas** (usuários, músicas e playlists)
implementado em **Python e Node.js** com quatro tecnologias — **REST, GraphQL, gRPC e SOAP**
(8 servidores + 8 clientes) — e comparado com **testes de carga**.

## Estrutura

```
python_api/         implementação completa em Python
  comum/            dados.py (repositório em memória), servidores.py (sobe os 8) e demonstracao.py
  rest/             servidor (FastAPI) + cliente (requests)
  graphql/          servidor (Strawberry) + cliente (requests)
  grpc/             musica.proto (compartilhado!) + servidor/cliente (grpcio)
  soap/             servidor (Spyne) + cliente (zeep)
node_api/           implementação completa em Node.js (espelho de python_api/)
  comum/            dados.js e demonstracao.js
  rest/             servidor (Express) + cliente (fetch)
  graphql/          servidor (graphql-http) + cliente (fetch)
  grpc/             servidor + cliente (@grpc/grpc-js)
  soap/             streaming.wsdl + servidor/cliente (node-soap)
testes/             81 testes automatizados: equivalência nos 8 servidores + interoperabilidade
testes_carga/       script k6, executor da bateria e gerador de gráficos
resultados/         CSV consolidado, gráficos e execuções arquivadas
```

Todos os servidores (tanto Python quanto Node.js) implementam exatamente o mesmo
modelo de dados (incluindo os atributos extras `email`, `genero`, `duracao_s` e
`descricao`) e o mesmo gerador determinístico. Assim, os 8 servidores começam
com os mesmos dados iniciais.

## Como executar

Pré-requisitos: [uv](https://docs.astral.sh/uv/) (instala o Python 3.11 e as
dependências Python) e **Node.js** (v20+). O Python 3.11 é necessário porque o
Spyne (SOAP) não funciona no 3.12+.

```bash
uv sync                                        # instala dependências Python
cd node_api && npm install && cd ..            # instala dependências Node.js
uv run python -m python_api.comum.servidores   # sobe os 8 servidores (Ctrl+C encerra)
```

Em outro terminal, rode qualquer cliente (Python ou Node.js):

```bash
uv run python -m python_api.rest.cliente
uv run python -m python_api.graphql.cliente
uv run python -m python_api.grpc.cliente
uv run python -m python_api.soap.cliente

node node_api/rest/cliente.js
node node_api/graphql/cliente.js
node node_api/grpc/cliente.js
node node_api/soap/cliente.js
```

| Tecnologia | Python | Node.js | Para explorar |
|---|---|---|---|
| REST | http://localhost:8001 | http://localhost:8101 | OpenAPI em `:8001/docs` |
| GraphQL | http://localhost:8002/graphql | http://localhost:8102/graphql | GraphiQL em `:8002/graphql` |
| gRPC | localhost:50051 | localhost:50151 | contrato único `python_api/grpc/musica.proto` |
| SOAP | http://localhost:8004 | http://localhost:8104 | WSDL em `/?wsdl` |

Se alterar o `musica.proto`, gere de novo o código Python do gRPC com
`python_api/grpc/gerar_codigo.sh` (o Node.js carrega o `.proto` dinamicamente).

### Testes automatizados

```bash
uv run pytest -v
```

Sobem os 8 servidores e executam **81 testes** verificando equivalência total
(as 5 consultas do enunciado, CRUD completo, regras de relacionamento e erros)
e interoperabilidade bidirecional (**Python ↔ Node.js**).

### Testes de carga

Usam o [k6](https://k6.io). Baixe o binário para `ferramentas/k6`:

```bash
mkdir -p ferramentas
curl -sL https://github.com/grafana/k6/releases/download/v2.3.0/k6-v2.3.0-linux-amd64.tar.gz \
  | tar xz -C ferramentas --strip-components=1
```

```bash
uv run python -m testes_carga.executar --rapido   # conferência (~5 min)
uv run python -m testes_carga.executar --enxuto   # bateria publicada: 2 reps × 3 s (~14 min, 2 linguagens)
uv run python -m testes_carga.executar            # bateria longa: 3 reps × 20 s (~110 min, 2 linguagens)
uv run python -m testes_carga.gerar_graficos      # gráficos em resultados/graficos/
```

Os resultados publicados para a entrega ficam protegidos em
`resultados/resultados.csv` (bateria enxuta de 2 repetições × 3 s para Python e
Node.js, com 1, 10, 50 e 100 usuários virtuais); novas execuções vão para
`resultados/execucoes/<data>_<tipo>/` para nunca sobrescrever a bateria principal.

- **leve:** consultas pequenas, sorteadas entre "playlists do usuário",
  "músicas da playlist" e "playlists que contêm a música";
- **pesada:** listar todas as 1000 músicas;
- **escrita:** criar, alterar e remover um usuário.

Para entender onde o tempo é gasto na carga pesada, há também um
microbenchmark que mede, sem rede, quanto cada biblioteca leva para gerar a
resposta com as 1000 músicas (salvo em `resultados/serializacao.json`):

```bash
taskset -c 2 uv run python -m testes_carga.medir_serializacao
```

O servidor roda nas CPUs 0–3 e o k6 nas CPUs 4–11, para o gerador de carga não
disputar CPU com o servidor medido. Ajuste `CPUS_SERVIDOR` e `CPUS_K6` em
`testes_carga/executar.py` se a sua máquina for diferente.
