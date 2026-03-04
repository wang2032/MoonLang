"""
Mooncake Transport Layer

Unified transport layer abstraction for Mooncake communication.
This module wraps the existing Mooncake implementation from disaggregation module.
"""

import logging
from typing import List, Optional, Tuple

import numpy as np
import numpy.typing as npt

from moonlang.srt.mooncake_core.config import MooncakeConfig
from moonlang.srt.distributed.parallel_state import get_mooncake_transfer_engine

logger = logging.getLogger(__name__)


class MooncakeTransportLayer:
    """
    Unified Mooncake transport layer for KV cache sharing.
    
    This class wraps the existing Mooncake implementation and provides:
    - Memory registration (reuses existing engine.batch_register)
    - KV cache transfer (reuses existing engine.batch_transfer_sync)
    - Integration with global cache metadata service
    """
    
    def __init__(self, config: MooncakeConfig):
        """
        Initialize Mooncake transport layer.
        
        Args:
            config: Mooncake configuration
        """
        self.config = config
        self.config.validate()
        
        # Reuse existing Mooncake transfer engine
        self.engine = None
        self.metadata_client = None
        self.registered_memory = {}  # ptr -> memory_id
        
        self._init_engine()
        
        if config.enable_global_cache:
            self._init_metadata_client()
    
    def _init_engine(self):
        """Initialize Mooncake transfer engine (reuse existing implementation)"""
        try:
            # Reuse the existing get_mooncake_transfer_engine from disaggregation
            self.engine = get_mooncake_transfer_engine()
            logger.info("Mooncake transfer engine initialized (reusing existing)")
        except Exception as e:
            logger.warning(f"Failed to initialize Mooncake engine: {e}")
            self.engine = None
    
    def _init_metadata_client(self):
        """Initialize metadata service client"""
        try:
            from moonlang.srt.mooncake_core.metadata_client import MetadataClient
            
            self.metadata_client = MetadataClient(
                server_addr=self.config.metadata_server_addr,
                timeout=self.config.cache_query_timeout,
            )
            logger.info(
                f"Connected to metadata server at {self.config.metadata_server_addr}"
            )
        except Exception as e:
            logger.warning(f"Failed to connect to metadata server: {e}")
            self.metadata_client = None
    
    def register_memory(self, ptr: int, size: int) -> Optional[str]:
        """
        Register GPU memory with Mooncake.
        
        Args:
            ptr: GPU memory pointer
            size: Memory size in bytes
            
        Returns:
            Memory ID if successful, None otherwise
        """
        if not self.engine:
            return None
        
        try:
            # Use existing engine.register (single memory region)
            # Note: The existing implementation uses batch_register
            self.engine.register(ptr, size)
            
            # Track registered memory
            memory_id = f"mem_{ptr}_{size}"
            self.registered_memory[ptr] = memory_id
            
            logger.debug(f"Registered memory: ptr={ptr}, size={size}")
            return memory_id
        except Exception as e:
            logger.error(f"Failed to register memory: {e}")
            return None
    
    def batch_register_memory(
        self, ptrs: List[int], sizes: List[int]
    ) -> List[Optional[str]]:
        """
        Batch register multiple memory regions (reuses existing implementation).
        
        Args:
            ptrs: List of GPU memory pointers
            sizes: List of memory sizes
            
        Returns:
            List of memory IDs
        """
        if not self.engine:
            return [None] * len(ptrs)
        
        try:
            # Reuse existing batch_register from MooncakeKVManager
            self.engine.batch_register(ptrs, sizes)
            
            # Track registered memory
            memory_ids = []
            for ptr, size in zip(ptrs, sizes):
                memory_id = f"mem_{ptr}_{size}"
                self.registered_memory[ptr] = memory_id
                memory_ids.append(memory_id)
            
            logger.debug(f"Batch registered {len(ptrs)} memory regions")
            return memory_ids
        except Exception as e:
            logger.error(f"Failed to batch register memory: {e}")
            return [None] * len(ptrs)
    
    def transfer_kv_cache(
        self,
        session_id: str,
        src_addrs: List[int],
        dst_addrs: List[int],
        lengths: List[int],
    ) -> bool:
        """
        Transfer KV cache from local to remote node (reuses existing implementation).
        
        Args:
            session_id: Mooncake session ID
            src_addrs: Source memory addresses (local)
            dst_addrs: Destination memory addresses (remote)
            lengths: Transfer lengths for each block
            
        Returns:
            True if transfer successful, False otherwise
        """
        if not self.engine:
            logger.warning("Mooncake engine not available, skipping transfer")
            return False
        
        if not src_addrs:
            return True
        
        try:
            # Reuse existing batch_transfer_sync from MooncakeKVManager
            status = self.engine.batch_transfer_sync(
                session_id, src_addrs, dst_addrs, lengths
            )
            
            if status == 0:
                logger.debug(
                    f"Successfully transferred {len(src_addrs)} KV cache blocks"
                )
                return True
            else:
                logger.error(f"Transfer failed with status {status}")
                return False
        except Exception as e:
            logger.error(f"Failed to transfer KV cache: {e}")
            return False
    
    def query_cache_location(self, prefix_hash: str) -> List[Tuple[str, List[int]]]:
        """
        Query which nodes have the given cache prefix.
        
        Args:
            prefix_hash: Hash of the cache prefix
            
        Returns:
            List of (node_id, kv_indices) tuples
        """
        if not self.metadata_client:
            return []
        
        try:
            locations = self.metadata_client.query_cache(prefix_hash)
            return [(loc["node_id"], loc["kv_indices"]) for loc in locations]
        except Exception as e:
            logger.error(f"Failed to query cache location: {e}")
            return []
    
    def register_cache(
        self, node_id: str, prefix_hash: str, kv_indices: List[int]
    ) -> bool:
        """
        Register local cache with metadata server.
        
        Args:
            node_id: Local node ID
            prefix_hash: Hash of the cache prefix
            kv_indices: KV cache indices
            
        Returns:
            True if registration successful, False otherwise
        """
        if not self.metadata_client:
            return False
        
        try:
            self.metadata_client.register_cache(node_id, prefix_hash, kv_indices)
            logger.debug(f"Registered cache: prefix={prefix_hash}, node={node_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register cache: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if Mooncake transport is available"""
        return self.engine is not None
    
    def is_global_cache_enabled(self) -> bool:
        """Check if global cache is enabled"""
        return self.config.enable_global_cache and self.metadata_client is not None


    def register_memory_addresses(
        self,
        node_id: str,
        endpoint: str,
        session_id: str,
        kv_data_ptrs: List[int],
        kv_item_lens: List[int],
    ) -> bool:
        """
        Register local memory addresses with metadata server.
        
        Phase 2: This allows other nodes to query our memory layout for RDMA transfer.
        
        Args:
            node_id: Local node ID
            endpoint: Local endpoint (IP address)
            session_id: Mooncake session ID
            kv_data_ptrs: Base pointers for KV data
            kv_item_lens: Item lengths for each layer
            
        Returns:
            True if registration successful
        """
        if not self.metadata_client:
            logger.warning("Metadata client not available")
            return False
        
        try:
            return self.metadata_client.register_memory_addresses(
                node_id=node_id,
                endpoint=endpoint,
                session_id=session_id,
                kv_data_ptrs=kv_data_ptrs,
                kv_item_lens=kv_item_lens,
            )
        except Exception as e:
            logger.error(f"Failed to register memory addresses: {e}")
            return False
    
    def query_memory_addresses(
        self, node_id: str, prefix_hash: str, kv_indices: List[int]
    ) -> dict:
        """
        Query memory addresses from a remote node.
        
        Phase 2: Get remote memory addresses for RDMA transfer.
        
        Args:
            node_id: Target node ID
            prefix_hash: Cache prefix hash
            kv_indices: KV cache indices
            
        Returns:
            Dictionary with memory addresses and connection info
        """
        if not self.metadata_client:
            logger.warning("Metadata client not available")
            return {
                "success": False,
                "memory_addresses": [],
                "endpoint": "",
                "session_id": "",
            }
        
        try:
            return self.metadata_client.query_memory_addresses(
                node_id=node_id,
                prefix_hash=prefix_hash,
                kv_indices=kv_indices,
            )
        except Exception as e:
            logger.error(f"Failed to query memory addresses: {e}")
            return {
                "success": False,
                "memory_addresses": [],
                "endpoint": "",
                "session_id": "",
            }
