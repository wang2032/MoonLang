"""
Test Phase 2: Remote KV Cache Transfer

This script tests the Phase 2 functionality:
1. Memory address registration
2. Memory address query
3. RDMA transfer simulation
"""

import argparse
import logging
import time
from typing import List

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def test_memory_registration():
    """Test memory address registration"""
    logger.info("Test 1: Memory address registration")
    
    from moonlang.srt.mooncake_core.metadata_client import MetadataClient
    
    client = MetadataClient("localhost:8999")
    
    # Simulate memory registration
    node_id = "test_node_1"
    endpoint = "192.168.1.100"
    session_id = "session_test_123"
    kv_data_ptrs = [0x1000000, 0x2000000, 0x3000000, 0x4000000]
    kv_item_lens = [4096, 4096, 4096, 4096]
    
    success = client.register_memory_addresses(
        node_id=node_id,
        endpoint=endpoint,
        session_id=session_id,
        kv_data_ptrs=kv_data_ptrs,
        kv_item_lens=kv_item_lens,
    )
    
    logger.info(f"✓ Memory registration result: {success}")
    return success


def test_memory_query():
    """Test memory address query"""
    logger.info("Test 2: Memory address query")
    
    from moonlang.srt.mooncake_core.metadata_client import MetadataClient
    
    client = MetadataClient("localhost:8999")
    
    # Query memory addresses
    node_id = "test_node_1"
    prefix_hash = "abc123"
    kv_indices = [0, 1, 2, 3, 4]
    
    result = client.query_memory_addresses(
        node_id=node_id,
        prefix_hash=prefix_hash,
        kv_indices=kv_indices,
    )
    
    logger.info(f"✓ Memory query result: success={result['success']}")
    logger.info(f"  - endpoint: {result['endpoint']}")
    logger.info(f"  - session_id: {result['session_id']}")
    logger.info(f"  - memory_addresses: {len(result['memory_addresses'])} entries")
    
    if result['memory_addresses']:
        first_addr = result['memory_addresses'][0]
        logger.info(f"  - first entry: kv_index={first_addr['kv_index']}, "
                   f"addresses={len(first_addr['addresses'])} layers")
    
    return result['success']


def test_e2e_flow():
    """Test end-to-end flow"""
    logger.info("Test 3: End-to-end flow")
    
    from moonlang.srt.mooncake_core.metadata_client import MetadataClient
    
    # Simulate two nodes
    client1 = MetadataClient("localhost:8999")
    client2 = MetadataClient("localhost:8999")
    
    # Node 1: Register memory and cache
    node1_id = "node_1"
    node1_endpoint = "192.168.1.100"
    node1_session = "session_node1"
    kv_data_ptrs = [0x1000000, 0x2000000, 0x3000000, 0x4000000]
    kv_item_lens = [4096, 4096, 4096, 4096]
    
    logger.info("Step 1: Node 1 registers memory addresses")
    success1 = client1.register_memory_addresses(
        node_id=node1_id,
        endpoint=node1_endpoint,
        session_id=node1_session,
        kv_data_ptrs=kv_data_ptrs,
        kv_item_lens=kv_item_lens,
    )
    logger.info(f"✓ Node 1 memory registration: {success1}")
    
    logger.info("Step 2: Node 1 registers cache")
    prefix_hash = "test_prefix_123"
    kv_indices = [0, 1, 2, 3, 4]
    success2 = client1.register_cache(
        node_id=node1_id,
        prefix_hash=prefix_hash,
        kv_indices=kv_indices,
    )
    logger.info(f"✓ Node 1 cache registration: {success2}")
    
    # Node 2: Query cache location
    logger.info("Step 3: Node 2 queries cache location")
    locations = client2.query_cache(prefix_hash)
    logger.info(f"✓ Node 2 found {len(locations)} cache locations")
    
    if locations:
        loc = locations[0]
        logger.info(f"  - node_id: {loc['node_id']}")
        logger.info(f"  - kv_indices: {len(loc['kv_indices'])} indices")
        
        # Node 2: Query memory addresses
        logger.info("Step 4: Node 2 queries memory addresses from Node 1")
        result = client2.query_memory_addresses(
            node_id=loc['node_id'],
            prefix_hash=prefix_hash,
            kv_indices=loc['kv_indices'],
        )
        
        logger.info(f"✓ Node 2 got memory addresses: success={result['success']}")
        logger.info(f"  - endpoint: {result['endpoint']}")
        logger.info(f"  - session_id: {result['session_id']}")
        logger.info(f"  - memory_addresses: {len(result['memory_addresses'])} entries")
        
        # Simulate RDMA transfer
        logger.info("Step 5: Node 2 would initiate RDMA transfer")
        logger.info(f"  - Source: {result['endpoint']} (session: {result['session_id']})")
        logger.info(f"  - Destination: Node 2 local memory")
        logger.info(f"  - Data: {len(result['memory_addresses'])} KV cache blocks")
        logger.info("  - Transfer: [SIMULATED - Phase 2 implementation]")
        
        return True
    else:
        logger.warning("No cache locations found")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test MoonLang Phase 2")
    parser.add_argument(
        "--test",
        type=str,
        choices=["registration", "query", "e2e", "all"],
        default="all",
        help="Which test to run",
    )
    parser.add_argument(
        "--server",
        type=str,
        default="localhost:8999",
        help="Metadata server address",
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("MoonLang Phase 2 Test Suite")
    logger.info("=" * 60)
    
    results = []
    
    if args.test in ["registration", "all"]:
        try:
            result = test_memory_registration()
            results.append(("Memory Registration", result))
        except Exception as e:
            logger.error(f"Memory registration test failed: {e}")
            results.append(("Memory Registration", False))
    
    if args.test in ["query", "all"]:
        try:
            result = test_memory_query()
            results.append(("Memory Query", result))
        except Exception as e:
            logger.error(f"Memory query test failed: {e}")
            results.append(("Memory Query", False))
    
    if args.test in ["e2e", "all"]:
        try:
            result = test_e2e_flow()
            results.append(("End-to-End Flow", result))
        except Exception as e:
            logger.error(f"E2E test failed: {e}")
            results.append(("End-to-End Flow", False))
    
    # Print summary
    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        logger.info("=" * 60)
        logger.info("✓ All Phase 2 tests passed!")
        logger.info("=" * 60)
    else:
        logger.error("=" * 60)
        logger.error("✗ Some Phase 2 tests failed")
        logger.error("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
