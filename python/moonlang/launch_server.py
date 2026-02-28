"""Launch the inference server."""

import asyncio
import os
import sys

from moonlang.srt.server_args import prepare_server_args
from moonlang.srt.utils import kill_process_tree
from moonlang.srt.utils.common import suppress_noisy_warnings

suppress_noisy_warnings()


def run_server(server_args):
    """Run the server based on server_args.grpc_mode and server_args.encoder_only."""
    if server_args.grpc_mode:
        from moonlang.srt.entrypoints.grpc_server import serve_grpc

        asyncio.run(serve_grpc(server_args))
    elif server_args.encoder_only:
        from moonlang.srt.disaggregation.encode_server import launch_server

        launch_server(server_args)
    else:
        # Default mode: HTTP mode.
        from moonlang.srt.entrypoints.http_server import launch_server

        launch_server(server_args)


if __name__ == "__main__":
    server_args = prepare_server_args(sys.argv[1:])

    try:
        run_server(server_args)
    finally:
        kill_process_tree(os.getpid(), include_parent=False)
