#!/usr/bin/env python3
"""
Test script for gRPC metadata service

Usage:
    # Terminal 1: Start server
    python test_grpc.py --mode server --port 8999
    
    # Terminal 2: Run client test
    python test_grpc.py --mode client --server localhost:8999
"""

import argparse
import logging
import time

from moonlang.srt.mooncake_core.metadata_client import MetadataClient
from moonlang.srt.mooncake_core.metadata_server import GlobalCacheMetadataServer

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def test_server(port: int):
    """Start metadata server"""
    logger.info(f"Starting metadata server on port {port}")
    server = GlobalCacheMetadataServer(port=port)
    server.start()


def test_client(server_addr: str):
    """Test metadata client"""
    logger.info(f"Connecting to metadata server at {server_addr}")
    
    client = MetadataClient(server_addr=server_addr, timeout=5.0)
    
    # Test 1: Register cache
    logger.info("Test 1: Register cache")
    success = client.register_cache(
        node_id="node_1",
        prefix_hash="test_prefix_123",
        kv_indices=[0, 1, 2, 3, 4],
    )
    logger.info(f"Register cache result: {success}")
    
    # Test 2: Query cache
    logger.info("Test 2: Query cache")
    locations = client.query_cache("test_prefix_123")
    logger.info(f"Query cache result: {locations}")
    
    # Test 3: Update node status
    logger.info("Test 3: Update node status")
    success = client.update_node_status(
        node_id="node_1",
        status={
            "available_memory": 16 * 1024 * 1024 * 1024,  # 16GB
            "total_memory": 32 * 1024 * 1024 * 1024,  # 32GB
            "active_requests": 5,
            "load_factor": 0.5,
        },
    )
    logger.info(f"Update node status result: {success}")
    
    # Test 4: Register another node
    logger.info("Test 4: Register cache from another node")
    success = client.register_cache(
        node_id="node_2",
        prefix_hash="test_prefix_123",
        kv_indices=[5, 6, 7, 8, 9],
    )
    logger.info(f"Register cache result: {success}")
    
    # Test 5: Query cache again (should see both nodes)
    logger.info("Test 5: Query cache again")
    locations = client.query_cache("test_prefix_123")
    logger.info(f"Query cache result: {locations}")
    logger.info(f"Found {len(locations)} nodes with this cache")
    
    # Test 6: Test local cache
    logger.info("Test 6: Test local cache (should hit local cache)")
    start_time = time.time()
    locations = client.query_cache("test_prefix_123")
    elapsed = time.time() - start_time
    logger.info(f"Query from local cache took {elapsed*1000:.2f}ms")
    
    # Test 7: Invalidate local cache
    logger.info("Test 7: Invalidate local cache")
    client.invalidate_cache("test_prefix_123")
    
    # Test 8: Query again (should query server)
    logger.info("Test 8: Query after invalidation (should query server)")
    start_time = time.time()
    locations = client.query_cache("test_prefix_123")
    elapsed = time.time() - start_time
    logger.info(f"Query from server took {elapsed*1000:.2f}ms")
    
    logger.info("All tests completed successfully!")
    client.close()


def main():
    parser = argparse.ArgumentParser(description="Test gRPC metadata service")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["server", "client"],
        required=True,
        help="Run mode: server or client",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8999,
        help="Server port (for server mode)",
    )
    parser.add_argument(
        "--server",
        type=str,
        default="localhost:8999",
        help="Server address (for client mode)",
    )
    
    args = parser.parse_args()
    
    if args.mode == "server":
        test_server(args.port)
    else:
        test_client(args.server)


if __name__ == "__main__":
    main()
