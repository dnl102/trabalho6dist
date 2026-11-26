#!/usr/bin/env bash
# Gera musica_pb2.py e musica_pb2_grpc.py a partir do contrato musica.proto.
# Rode na raiz do projeto sempre que alterar o .proto.
set -euo pipefail
cd "$(dirname "$0")/../.."
uv run python -m grpc_tools.protoc -I . \
  --python_out=. --pyi_out=. --grpc_python_out=. \
  python_api/grpc/musica.proto
echo "Código gerado em python_api/grpc/"
