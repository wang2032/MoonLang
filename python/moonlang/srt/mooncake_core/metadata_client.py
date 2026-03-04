"""
Metadata Service Client

Client for communicating with the global cache metadata server.
"""

import logging
import time
from typing import Dict, List, Optional

try:
    import grpc
    # Direct import to avoid __init__.py issues
    import moonlang.srt.mooncake_core.metadata_pb2 as metadata_pb2
    import moonlang.srt.mooncake_core.metadata_pb2_grpc as metadata_pb2_grpc
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    grpc = None
    metadata_pb2 = None
    metadata_pb2_grpc = None

logger = logging.getLogger(__name__)


class MetadataClient:
    """
    Client for global cache metadata service.
    
    Provides methods to:
    - Query cache locations
    - Register local cache
    - Update node status
    """
    
    def __init__(self, server_addr: str, timeout: float = 1.0):
        """
        Initialize metadata client.
        
        Args:
            server_addr: Metadata server address (ip:port)
            timeout: Request timeout in seconds
        """
        self.server_addr = server_addr
        self.timeout = timeout
        self.local_cache = {}  # prefix_hash -> cache_info
        self.cache_ttl = 60.0  # seconds
        
        # Initialize gRPC channel and stub
        if GRPC_AVAILABLE:
            self.channel = grpc.insecure_channel(
                server_addr,
                options=[
                    ("grpc.max_send_message_length", 100 * 1024 * 1024),
                    ("grpc.max_receive_message_length", 100 * 1024 * 1024),
                ],
            )
            self.stub = metadata_pb2_grpc.MetadataServiceStub(self.channel)
            logger.info(f"Metadata client initialized for {server_addr}")
        else:
            self.channel = None
            self.stub = None
            logger.warning(
                "gRPC is not available. Metadata client will not function. "
                "Please install grpcio: pip install grpcio"
            )
    
    def query_cache(self, prefix_hash: str) -> List[Dict]:
        """
        Query which nodes have the given cache prefix.
        
        Args:
            prefix_hash: Hash of the cache prefix
            
        Returns:
            List of cache location info:
            [
                {
                    'node_id': str,
                    'kv_indices': List[int],
                    'timestamp': float
                },
                ...
            ]
        """
        # Check local cache first
        if prefix_hash in self.local_cache:
            cached_info = self.local_cache[prefix_hash]
            if time.time() - cached_info["cached_at"] < self.cache_ttl:
                logger.debug(f"Cache hit for prefix {prefix_hash} (local)")
                return cached_info["locations"]
        
        # Query from metadata server
        if not self.stub:
            logger.warning("gRPC stub not available, cannot query cache")
            return []
        
        try:
            request = metadata_pb2.QueryCacheRequest(prefix_hash=prefix_hash)
            response = self.stub.QueryCache(request, timeout=self.timeout)
            
            # Convert response to dict format
            locations = []
            for loc in response.locations:
                locations.append({
                    "node_id": loc.node_id,
                    "kv_indices": list(loc.kv_indices),
                    "timestamp": loc.timestamp,
                })
            
            # Update local cache
            self.local_cache[prefix_hash] = {
                "locations": locations,
                "cached_at": time.time(),
            }
            
            logger.debug(
                f"Query cache: prefix={prefix_hash}, found={len(locations)} locations"
            )
            return locations
        except grpc.RpcError as e:
            logger.error(f"Failed to query cache from metadata server: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error querying cache: {e}")
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
        if not self.stub:
            logger.warning("gRPC stub not available, cannot register cache")
            return False
        
        try:
            request = metadata_pb2.RegisterCacheRequest(
                node_id=node_id,
                prefix_hash=prefix_hash,
                kv_indices=kv_indices,
            )
            response = self.stub.RegisterCache(request, timeout=self.timeout)
            
            if response.success:
                logger.debug(
                    f"Registered cache: node={node_id}, prefix={prefix_hash}, "
                    f"indices={len(kv_indices)}"
                )
            else:
                logger.warning(f"Failed to register cache: {response.message}")
            
            return response.success
        except grpc.RpcError as e:
            logger.error(f"Failed to register cache: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error registering cache: {e}")
            return False
    
    def update_node_status(self, node_id: str, status: Dict) -> bool:
        """
        Update node status in metadata server.
        
        Args:
            node_id: Node ID
            status: Node status info (capacity, load, etc.)
            
        Returns:
            True if update successful, False otherwise
        """
        if not self.stub:
            logger.warning("gRPC stub not available, cannot update node status")
            return False
        
        try:
            node_status = metadata_pb2.NodeStatus(
                available_memory=status.get("available_memory", 0),
                total_memory=status.get("total_memory", 0),
                active_requests=status.get("active_requests", 0),
                load_factor=status.get("load_factor", 0.0),
            )
            
            request = metadata_pb2.UpdateNodeStatusRequest(
                node_id=node_id,
                status=node_status,
            )
            response = self.stub.UpdateNodeStatus(request, timeout=self.timeout)
            
            return response.success
        except grpc.RpcError as e:
            logger.error(f"Failed to update node status: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating node status: {e}")
            return False
    
    def invalidate_cache(self, prefix_hash: Optional[str] = None):
        """
        Invalidate local cache.
        
        Args:
            prefix_hash: Specific prefix to invalidate, or None for all
        """
        if prefix_hash:
            self.local_cache.pop(prefix_hash, None)
        else:
            self.local_cache.clear()
    
    def close(self):
        """Close the gRPC channel"""
        if self.channel:
            self.channel.close()
    
    def query_memory_addresses(
        self, node_id: str, prefix_hash: str, kv_indices: List[int]
    ) -> Dict:
        """
        Query memory addresses for KV cache indices on a remote node.
        
        Phase 2: This enables RDMA transfer by getting remote memory addresses.
        
        Args:
            node_id: Target node ID
            prefix_hash: Cache prefix hash
            kv_indices: KV cache indices to query
            
        Returns:
            Dictionary with:
            - success: bool
            - memory_addresses: List[Dict] with kv_index and addresses
            - endpoint: str (node IP address)
            - session_id: str (Mooncake session ID)
        """
        if not self.stub:
            logger.warning("gRPC stub not available, cannot query memory addresses")
            return {
                "success": False,
                "memory_addresses": [],
                "endpoint": "",
                "session_id": "",
            }
        
        try:
            request = metadata_pb2.QueryMemoryAddressesRequest(
                node_id=node_id,
                prefix_hash=prefix_hash,
                kv_indices=kv_indices,
            )
            response = self.stub.QueryMemoryAddresses(request, timeout=self.timeout)
            
            # Convert response to dict format
            memory_addresses = []
            for mem_addr in response.memory_addresses:
                memory_addresses.append({
                    "kv_index": mem_addr.kv_index,
                    "addresses": list(mem_addr.addresses),
                })
            
            result = {
                "success": response.success,
                "memory_addresses": memory_addresses,
                "endpoint": response.endpoint,
                "session_id": response.session_id,
            }
            
            logger.debug(
                f"Query memory addresses: node={node_id}, "
                f"indices={len(kv_indices)}, success={response.success}"
            )
            
            return result
        except grpc.RpcError as e:
            logger.error(f"Failed to query memory addresses: {e}")
            return {
                "success": False,
                "memory_addresses": [],
                "endpoint": "",
                "session_id": "",
            }
        except Exception as e:
            logger.error(f"Unexpected error querying memory addresses: {e}")
            return {
                "success": False,
                "memory_addresses": [],
                "endpoint": "",
                "session_id": "",
            }
    
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
        
        Phase 2: This allows other nodes to query our memory addresses for RDMA.
        
        Args:
            node_id: Local node ID
            endpoint: Local endpoint (IP address)
            session_id: Mooncake session ID
            kv_data_ptrs: Base pointers for KV data
            kv_item_lens: Item lengths for each layer
            
        Returns:
            True if registration successful
        """
        if not self.stub:
            logger.warning("gRPC stub not available, cannot register memory addresses")
            return False
        
        try:
            request = metadata_pb2.RegisterMemoryAddressesRequest(
                node_id=node_id,
                endpoint=endpoint,
                session_id=session_id,
                kv_data_ptrs=kv_data_ptrs,
                kv_item_lens=kv_item_lens,
            )
            response = self.stub.RegisterMemoryAddresses(request, timeout=self.timeout)
            
            if response.success:
                logger.info(
                    f"Registered memory addresses: node={node_id}, "
                    f"endpoint={endpoint}, ptrs={len(kv_data_ptrs)}"
                )
            else:
                logger.warning(f"Failed to register memory addresses: {response.message}")
            
            return response.success
        except grpc.RpcError as e:
            logger.error(f"Failed to register memory addresses: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error registering memory addresses: {e}")
            return False
