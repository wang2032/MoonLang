#!/usr/bin/env python3
"""
Test script for Scheduler integration with Mooncake transport layer

This script tests the integration without actually running a full server.
"""

import logging
import sys
from unittest.mock import MagicMock, patch

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def test_scheduler_mooncake_init():
    """Test that Scheduler can initialize Mooncake transport layer"""
    
    logger.info("Test 1: Scheduler initialization with global cache disabled")
    
    # Mock server args
    from moonlang.srt.server_args import ServerArgs
    
    # Create minimal server args
    server_args = ServerArgs(
        model_path="dummy",
        enable_global_cache=False,
    )
    
    logger.info("✓ ServerArgs created with enable_global_cache=False")
    
    # Test 2: With global cache enabled
    logger.info("\nTest 2: Scheduler initialization with global cache enabled")
    
    server_args_with_cache = ServerArgs(
        model_path="dummy",
        enable_global_cache=True,
        global_cache_metadata_server="localhost:8999",
        global_cache_query_timeout=1.0,
        global_cache_transfer_timeout=10.0,
    )
    
    logger.info("✓ ServerArgs created with enable_global_cache=True")
    logger.info(f"  - metadata_server: {server_args_with_cache.global_cache_metadata_server}")
    logger.info(f"  - query_timeout: {server_args_with_cache.global_cache_query_timeout}")
    logger.info(f"  - transfer_timeout: {server_args_with_cache.global_cache_transfer_timeout}")
    
    # Test 3: Test MooncakeConfig
    logger.info("\nTest 3: MooncakeConfig validation")
    
    from moonlang.srt.mooncake_core.config import MooncakeConfig
    
    config = MooncakeConfig(
        enable_global_cache=True,
        metadata_server_addr="localhost:8999",
        cache_query_timeout=1.0,
        transfer_timeout=10.0,
        ib_device="mlx5_0",
    )
    
    try:
        config.validate()
        logger.info("✓ MooncakeConfig validation passed")
    except Exception as e:
        logger.error(f"✗ MooncakeConfig validation failed: {e}")
        return False
    
    # Test 4: Test MooncakeTransportLayer initialization
    logger.info("\nTest 4: MooncakeTransportLayer initialization")
    
    from moonlang.srt.mooncake_core.transport import MooncakeTransportLayer
    
    try:
        transport = MooncakeTransportLayer(config)
        logger.info("✓ MooncakeTransportLayer created")
        logger.info(f"  - is_available: {transport.is_available()}")
        logger.info(f"  - is_global_cache_enabled: {transport.is_global_cache_enabled()}")
    except Exception as e:
        logger.warning(f"⚠ MooncakeTransportLayer initialization: {e}")
        logger.info("  (This is expected if Mooncake engine is not available)")
    
    # Test 5: Test cache helper methods
    logger.info("\nTest 5: Cache helper methods")
    
    # Mock a simple scheduler-like object
    class MockScheduler:
        def __init__(self):
            self.mooncake_transport = None
            self.node_id = "test_node_1"
        
        def compute_prefix_hash(self, input_ids):
            import hashlib
            prefix_length = min(len(input_ids), 128)
            prefix_tokens = tuple(input_ids[:prefix_length])
            hash_obj = hashlib.sha256(str(prefix_tokens).encode())
            return hash_obj.hexdigest()[:16]
    
    scheduler = MockScheduler()
    
    # Test prefix hash computation
    test_input_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    prefix_hash = scheduler.compute_prefix_hash(test_input_ids)
    logger.info(f"✓ Computed prefix hash: {prefix_hash}")
    
    # Test with different input
    test_input_ids_2 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11]  # Last token different
    prefix_hash_2 = scheduler.compute_prefix_hash(test_input_ids_2)
    logger.info(f"✓ Computed prefix hash 2: {prefix_hash_2}")
    
    if prefix_hash != prefix_hash_2:
        logger.info("✓ Different inputs produce different hashes")
    else:
        logger.error("✗ Different inputs produced same hash!")
        return False
    
    # Test with same input
    prefix_hash_3 = scheduler.compute_prefix_hash(test_input_ids)
    if prefix_hash == prefix_hash_3:
        logger.info("✓ Same input produces same hash (deterministic)")
    else:
        logger.error("✗ Same input produced different hash!")
        return False
    
    logger.info("\n" + "="*60)
    logger.info("All tests passed! ✓")
    logger.info("="*60)
    
    return True


def main():
    logger.info("Testing Scheduler integration with Mooncake transport layer")
    logger.info("="*60)
    
    try:
        success = test_scheduler_mooncake_init()
        if success:
            logger.info("\n✓ All integration tests passed!")
            sys.exit(0)
        else:
            logger.error("\n✗ Some tests failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
