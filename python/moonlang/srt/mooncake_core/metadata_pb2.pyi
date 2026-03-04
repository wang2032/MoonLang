from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class QueryCacheRequest(_message.Message):
    __slots__ = ("prefix_hash",)
    PREFIX_HASH_FIELD_NUMBER: _ClassVar[int]
    prefix_hash: str
    def __init__(self, prefix_hash: _Optional[str] = ...) -> None: ...

class CacheLocation(_message.Message):
    __slots__ = ("node_id", "kv_indices", "timestamp")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    KV_INDICES_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    node_id: str
    kv_indices: _containers.RepeatedScalarFieldContainer[int]
    timestamp: float
    def __init__(self, node_id: _Optional[str] = ..., kv_indices: _Optional[_Iterable[int]] = ..., timestamp: _Optional[float] = ...) -> None: ...

class QueryCacheResponse(_message.Message):
    __slots__ = ("locations",)
    LOCATIONS_FIELD_NUMBER: _ClassVar[int]
    locations: _containers.RepeatedCompositeFieldContainer[CacheLocation]
    def __init__(self, locations: _Optional[_Iterable[_Union[CacheLocation, _Mapping]]] = ...) -> None: ...

class RegisterCacheRequest(_message.Message):
    __slots__ = ("node_id", "prefix_hash", "kv_indices")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    PREFIX_HASH_FIELD_NUMBER: _ClassVar[int]
    KV_INDICES_FIELD_NUMBER: _ClassVar[int]
    node_id: str
    prefix_hash: str
    kv_indices: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, node_id: _Optional[str] = ..., prefix_hash: _Optional[str] = ..., kv_indices: _Optional[_Iterable[int]] = ...) -> None: ...

class RegisterCacheResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class NodeStatus(_message.Message):
    __slots__ = ("available_memory", "total_memory", "active_requests", "load_factor")
    AVAILABLE_MEMORY_FIELD_NUMBER: _ClassVar[int]
    TOTAL_MEMORY_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_REQUESTS_FIELD_NUMBER: _ClassVar[int]
    LOAD_FACTOR_FIELD_NUMBER: _ClassVar[int]
    available_memory: int
    total_memory: int
    active_requests: int
    load_factor: float
    def __init__(self, available_memory: _Optional[int] = ..., total_memory: _Optional[int] = ..., active_requests: _Optional[int] = ..., load_factor: _Optional[float] = ...) -> None: ...

class UpdateNodeStatusRequest(_message.Message):
    __slots__ = ("node_id", "status")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    node_id: str
    status: NodeStatus
    def __init__(self, node_id: _Optional[str] = ..., status: _Optional[_Union[NodeStatus, _Mapping]] = ...) -> None: ...

class UpdateNodeStatusResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...
