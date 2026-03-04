"""
Global Cache Metadata Server

Centralized metadata service for tracking KV cache locations across nodes.
"""

import argparse
import logging
import time
from collections import defaultdict
from concurrent import futures
from typing import Dict, List

logger = logging.getLogger(__name__)


class GlobalCacheMetadataServer:
    """
    Global metadata server for KV cache sharing.
    
    Tracks:
    - Which nodes have which cache prefixes
    - Node status and capacity
    - Cache access patterns
    """
    
    def __init__(self, port: int = 8999):
        """
        Initialize metadata server.
        
        Args:
            port: Server port
        """
        self.port = port
        
        # Cache registry: prefix_hash -> list of node info
        self.cache_registry: Dict[str, List[Dict]] = defaultdict(list)
        
        # Node registry: node_id -> node info
        self.node_registry: Dict[str, Dict] = {}
        
        # Phase 2: Memory registry: node_id -> memory info
        self.memory_registry: Dict[str, Dict] = {}
        
        # Access statistics
        self.access_stats: Dict[str, int] = defaultdict(int)
        
        # gRPC server
        self.grpc_server = None
        
        logger.info(f"Metadata server initialized on port {port}")
    
    def register_cache(
        self, node_id: str, prefix_hash: str, kv_indices: List[int]
    ) -> bool:
        """
        Register cache from a node.
        
        Args:
            node_id: Node ID
            prefix_hash: Cache prefix hash
            kv_indices: KV cache indices
            
        Returns:
            True if registration successful
        """
        try:
            # Check if already registered
            existing = [
                entry
                for entry in self.cache_registry[prefix_hash]
                if entry["node_id"] == node_id
            ]
            
            if existing:
                # Update existing entry
                existing[0]["kv_indices"] = kv_indices
                existing[0]["timestamp"] = time.time()
            else:
                # Add new entry
                self.cache_registry[prefix_hash].append(
                    {
                        "node_id": node_id,
                        "kv_indices": kv_indices,
                        "timestamp": time.time(),
                    }
                )
            
            logger.debug(
                f"Registered cache: node={node_id}, prefix={prefix_hash}, "
                f"indices={len(kv_indices)}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to register cache: {e}")
            return False
    
    def query_cache(self, prefix_hash: str) -> List[Dict]:
        """
        Query cache locations.
        
        Args:
            prefix_hash: Cache prefix hash
            
        Returns:
            List of cache location info
        """
        # Update access statistics
        self.access_stats[prefix_hash] += 1
        
        # Return cache locations
        locations = self.cache_registry.get(prefix_hash, [])
        
        logger.debug(
            f"Query cache: prefix={prefix_hash}, found={len(locations)} locations"
        )
        
        return locations
    
    def update_node_status(self, node_id: str, status: Dict) -> bool:
        """
        Update node status.
        
        Args:
            node_id: Node ID
            status: Node status info
            
        Returns:
            True if update successful
        """
        try:
            self.node_registry[node_id] = {
                **status,
                "last_update": time.time(),
            }
            
            logger.debug(f"Updated node status: node={node_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update node status: {e}")
            return False
    
    def get_node_status(self, node_id: str) -> Dict:
        """Get node status"""
        return self.node_registry.get(node_id, {})
    
    def get_all_nodes(self) -> List[str]:
        """Get all registered nodes"""
        return list(self.node_registry.keys())
    
    def get_statistics(self) -> Dict:
        """Get server statistics"""
        return {
            "total_cache_entries": len(self.cache_registry),
            "total_nodes": len(self.node_registry),
            "total_memory_registrations": len(self.memory_registry),
            "total_queries": sum(self.access_stats.values()),
            "top_accessed": sorted(
                self.access_stats.items(), key=lambda x: x[1], reverse=True
            )[:10],
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
        Register node's memory addresses for RDMA transfer.
        
        Args:
            node_id: Node ID
            endpoint: Node endpoint (IP address)
            session_id: Mooncake session ID
            kv_data_ptrs: Base pointers for KV data
            kv_item_lens: Item lengths for each layer
            
        Returns:
            True if registration successful
        """
        try:
            self.memory_registry[node_id] = {
                "endpoint": endpoint,
                "session_id": session_id,
                "kv_data_ptrs": kv_data_ptrs,
                "kv_item_lens": kv_item_lens,
                "last_update": time.time(),
            }
            
            logger.info(
                f"Registered memory addresses: node={node_id}, "
                f"endpoint={endpoint}, ptrs={len(kv_data_ptrs)}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to register memory addresses: {e}")
            return False
    
    def query_memory_addresses(
        self, node_id: str, prefix_hash: str, kv_indices: List[int]
    ) -> Dict:
        """
        Query memory addresses for KV cache indices on a specific node.
        
        Args:
            node_id: Target node ID
            prefix_hash: Cache prefix hash
            kv_indices: KV cache indices to query
            
        Returns:
            Dictionary with memory addresses and connection info
        """
        if node_id not in self.memory_registry:
            logger.warning(f"Node {node_id} not found in memory registry")
            return {
                "success": False,
                "memory_addresses": [],
                "endpoint": "",
                "session_id": "",
            }
        
        try:
            mem_info = self.memory_registry[node_id]
            kv_data_ptrs = mem_info["kv_data_ptrs"]
            kv_item_lens = mem_info["kv_item_lens"]
            
            # Calculate memory addresses for each KV index
            memory_addresses = []
            for kv_idx in kv_indices:
                addresses = []
                # For each layer, calculate address
                for layer_id in range(len(kv_data_ptrs)):
                    base_ptr = kv_data_ptrs[layer_id]
                    item_len = kv_item_lens[layer_id]
                    addr = base_ptr + kv_idx * item_len
                    addresses.append(addr)
                
                memory_addresses.append({
                    "kv_index": kv_idx,
                    "addresses": addresses,
                })
            
            logger.debug(
                f"Query memory addresses: node={node_id}, "
                f"indices={len(kv_indices)}, addresses={len(memory_addresses)}"
            )
            
            return {
                "success": True,
                "memory_addresses": memory_addresses,
                "endpoint": mem_info["endpoint"],
                "session_id": mem_info["session_id"],
            }
        except Exception as e:
            logger.error(f"Failed to query memory addresses: {e}")
            return {
                "success": False,
                "memory_addresses": [],
                "endpoint": "",
                "session_id": "",
            }
    
    def cleanup_stale_entries(self, max_age: float = 300.0):
        """
        Clean up stale cache entries.
        
        Args:
            max_age: Maximum age in seconds
        """
        current_time = time.time()
        removed_count = 0
        
        for prefix_hash in list(self.cache_registry.keys()):
            entries = self.cache_registry[prefix_hash]
            
            # Filter out stale entries
            fresh_entries = [
                entry
                for entry in entries
                if current_time - entry["timestamp"] < max_age
            ]
            
            if fresh_entries:
                self.cache_registry[prefix_hash] = fresh_entries
            else:
                del self.cache_registry[prefix_hash]
                removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} stale cache entries")
    
    def start(self):
        """Start the metadata server"""
        # Import gRPC modules here to avoid circular import
        try:
            import grpc
            # Direct import to avoid __init__.py issues
            import moonlang.srt.mooncake_core.metadata_pb2 as metadata_pb2
            import moonlang.srt.mooncake_core.metadata_pb2_grpc as metadata_pb2_grpc
        except ImportError as e:
            logger.error(
                f"gRPC is not available: {e}. "
                "Please install grpcio and grpcio-tools: pip install grpcio grpcio-tools"
            )
            return
        
        logger.info(f"Starting metadata server on port {self.port}")
        
        # Create gRPC server
        self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        
        # Create servicer class dynamically to avoid import issues
        server_instance = self
        
        class MetadataServicer(metadata_pb2_grpc.MetadataServiceServicer):
            """gRPC servicer implementation"""
            
            def QueryCache(self, request, context):
                """Handle QueryCache RPC"""
                locations = server_instance.query_cache(request.prefix_hash)
                
                response = metadata_pb2.QueryCacheResponse()
                for loc in locations:
                    cache_loc = response.locations.add()
                    cache_loc.node_id = loc["node_id"]
                    cache_loc.kv_indices.extend(loc["kv_indices"])
                    cache_loc.timestamp = loc["timestamp"]
                
                return response
            
            def RegisterCache(self, request, context):
                """Handle RegisterCache RPC"""
                success = server_instance.register_cache(
                    request.node_id,
                    request.prefix_hash,
                    list(request.kv_indices),
                )
                
                return metadata_pb2.RegisterCacheResponse(
                    success=success,
                    message="Cache registered successfully" if success else "Registration failed",
                )
            
            def UpdateNodeStatus(self, request, context):
                """Handle UpdateNodeStatus RPC"""
                status = {
                    "available_memory": request.status.available_memory,
                    "total_memory": request.status.total_memory,
                    "active_requests": request.status.active_requests,
                    "load_factor": request.status.load_factor,
                }
                
                success = server_instance.update_node_status(request.node_id, status)
                
                return metadata_pb2.UpdateNodeStatusResponse(success=success)
            
            def QueryMemoryAddresses(self, request, context):
                """Handle QueryMemoryAddresses RPC (Phase 2)"""
                result = server_instance.query_memory_addresses(
                    request.node_id,
                    request.prefix_hash,
                    list(request.kv_indices),
                )
                
                response = metadata_pb2.QueryMemoryAddressesResponse()
                response.success = result["success"]
                response.endpoint = result["endpoint"]
                response.session_id = result["session_id"]
                
                for mem_addr in result["memory_addresses"]:
                    addr_msg = response.memory_addresses.add()
                    addr_msg.kv_index = mem_addr["kv_index"]
                    addr_msg.addresses.extend(mem_addr["addresses"])
                
                return response
            
            def RegisterMemoryAddresses(self, request, context):
                """Handle RegisterMemoryAddresses RPC (Phase 2)"""
                success = server_instance.register_memory_addresses(
                    request.node_id,
                    request.endpoint,
                    request.session_id,
                    list(request.kv_data_ptrs),
                    list(request.kv_item_lens),
                )
                
                return metadata_pb2.RegisterMemoryAddressesResponse(
                    success=success,
                    message="Memory addresses registered successfully" if success else "Registration failed",
                )
        
        # Add servicer
        metadata_pb2_grpc.add_MetadataServiceServicer_to_server(
            MetadataServicer(), self.grpc_server
        )
        
        # Bind to port
        self.grpc_server.add_insecure_port(f"[::]:{self.port}")
        
        # Start server
        self.grpc_server.start()
        logger.info(f"Metadata server running on port {self.port}")
        
        try:
            # Keep server running
            self.grpc_server.wait_for_termination()
        except KeyboardInterrupt:
            logger.info("Shutting down metadata server")
            self.grpc_server.stop(0)


def main():
    """Main entry point for metadata server"""
    parser = argparse.ArgumentParser(description="MoonLang Global Cache Metadata Server")
    parser.add_argument("--port", type=int, default=8999, help="Server port")
    parser.add_argument(
        "--log-level", type=str, default="INFO", help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="[%(asctime)s] %(levelname)s: %(message)s",
    )
    
    # Create and start server
    server = GlobalCacheMetadataServer(port=args.port)
    server.start()


if __name__ == "__main__":
    main()
