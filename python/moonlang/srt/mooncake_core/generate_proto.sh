#!/bin/bash
# Generate Python code from protobuf definition

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Generate Python code
python -m grpc_tools.protoc \
    -I"$SCRIPT_DIR" \
    --python_out="$SCRIPT_DIR" \
    --grpc_python_out="$SCRIPT_DIR" \
    "$SCRIPT_DIR/metadata.proto"

echo "Generated metadata_pb2.py and metadata_pb2_grpc.py"
