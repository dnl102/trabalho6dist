"""
Microbenchmark: quanto tempo cada biblioteca gasta só para GERAR a resposta
de "listar as 1000 músicas" (sem rede, sem servidor HTTP).

Serve para testar a hipótese da análise: na carga pesada, o custo de
transformar objetos Python em mensagens explica boa parte das diferenças.

Uso:  taskset -c 2 uv run python -m testes_carga.medir_serializacao
Saída: resultados/serializacao.json
"""

import json
import statistics
import time
from pathlib import Path

from python_api.comum.dados import criar_repositorio_populado


def medir(nome, funcao, repeticoes=200):
    funcao()  # aquecimento
    tempos = []
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        funcao()
        tempos.append((time.perf_counter() - inicio) * 1000)
    mediana = statistics.median(tempos)
    print(f"{nome:10} {mediana:8.2f} ms por resposta  (~{1000 / mediana:7.0f} respostas/s em 1 núcleo)")
    return mediana


def main():
    resultado = {}
    repo = criar_repositorio_populado()
    musicas = repo.listar_musicas()

    # REST: o FastAPI serializa o tipo de retorno com o pydantic-core (Rust)
    from pydantic import TypeAdapter
    from python_api.comum.dados import Musica
    adaptador = TypeAdapter(list[Musica])
    resultado["rest"] = medir("REST", lambda: adaptador.dump_json(musicas))

    # gRPC: monta as mensagens protobuf e serializa em binário
    from python_api.grpc import musica_pb2 as pb
    from python_api.grpc.servidor import musica_pb
    resultado["grpc"] = medir("gRPC", lambda: pb.ListaMusicas(
        musicas=[musica_pb(m) for m in musicas]).SerializeToString())

    # GraphQL: executa a consulta inteira no esquema (análise, validação, resolvers)
    from python_api.graphql.servidor import schema
    resultado["graphql"] = medir("GraphQL", lambda: json.dumps(
        schema.execute_sync("{ musicas { id nome artista genero duracaoS } }").data), repeticoes=50)

    # SOAP: o Spyne processa a chamada completa (lê o envelope XML,
    # executa a operação e gera o XML de resposta)
    from python_api.soap.servidor import app as wsgi_soap
    import io
    envelope = (b'<?xml version="1.0" encoding="UTF-8"?>'
                b'<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
                b'xmlns:s="http://exemplo.ufc.br/streaming"><soapenv:Body><s:ListarMusicas/>'
                b'</soapenv:Body></soapenv:Envelope>')

    def chamar_soap():
        ambiente = {"REQUEST_METHOD": "POST", "PATH_INFO": "/", "QUERY_STRING": "",
                    "CONTENT_TYPE": "text/xml; charset=utf-8",
                    "CONTENT_LENGTH": str(len(envelope)), "wsgi.input": io.BytesIO(envelope),
                    "SERVER_NAME": "localhost", "SERVER_PORT": "8004", "wsgi.url_scheme": "http",
                    "HTTP_SOAPACTION": '"ListarMusicas"'}
        corpo = b"".join(wsgi_soap(ambiente, lambda *a, **k: None))
        assert b"ListarMusicasResponse" in corpo
    resultado["soap"] = medir("SOAP", chamar_soap, repeticoes=50)

    saida = Path(__file__).resolve().parent.parent / "resultados" / "serializacao.json"
    saida.write_text(json.dumps({"ms_por_resposta_1000_musicas": resultado}, indent=2))
    print(f"Salvo em {saida}")


if __name__ == "__main__":
    main()
