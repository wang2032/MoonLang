"""
Mooncake Configuration

Configuration classes for Mooncake integration.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MooncakeConfig:
    """Configuration for Mooncake integration"""
    
    # Enable global cache sharing
    enable_global_cache: bool = False
    
    # Metadata server address (ip:port)
    metadata_server_addr: Optional[str] = None
    
    # InfiniBand device name
    ib_device: Optional[str] = None
    
    # Metadata server port (when running as metadata server)
    metadata_server_port: int = 8999
    
    # Cache query timeout (seconds)
    cache_query_timeout: float = 1.0
    
    # Cache transfer timeout (seconds)
    cache_transfer_timeout: float = 10.0
    
    # Enable local cache for metadata
    enable_metadata_cache: bool = True
    
    # Metadata cache TTL (seconds)
    metadata_cache_ttl: float = 60.0
    
    def validate(self):
        """Validate configuration"""
        if self.enable_global_cache:
            if not self.metadata_server_addr:
                raise ValueError(
                    "metadata_server_addr is required when enable_global_cache=True"
                )
            if not self.ib_device:
                raise ValueError(
                    "ib_device is required when enable_global_cache=True"
                )
