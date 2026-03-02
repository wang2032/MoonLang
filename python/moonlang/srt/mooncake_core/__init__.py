"""
MoonLang Mooncake Core Module

This module provides the core infrastructure for Mooncake integration,
including transport layer, metadata service, and cache registry.
"""

from moonlang.srt.mooncake_core.config import MooncakeConfig
from moonlang.srt.mooncake_core.metadata_client import MetadataClient
from moonlang.srt.mooncake_core.metadata_server import GlobalCacheMetadataServer
from moonlang.srt.mooncake_core.transport import MooncakeTransportLayer

# Try to import generated protobuf modules
try:
    from moonlang.srt.mooncake_core import metadata_pb2, metadata_pb2_grpc
except ImportError:
    # Protobuf files not generated yet
    metadata_pb2 = None
    metadata_pb2_grpc = None

__all__ = [
    "MooncakeConfig",
    "MooncakeTransportLayer",
    "MetadataClient",
    "GlobalCacheMetadataServer",
    "metadata_pb2",
    "metadata_pb2_grpc",
]

