# MoonLang Mooncake Core Module

全局KV缓存共享的核心模块，基于Mooncake实现跨节点缓存传输。

## 模块结构

```
mooncake_core/
├── __init__.py              # 模块导出
├── config.py                # Mooncake配置
├── transport.py             # 传输层（复用现有Mooncake引擎）
├── metadata_client.py       # 元数据客户端（gRPC）
├── metadata_server.py       # 元数据服务器（gRPC）
├── metadata.proto           # Protobuf定义
├── generate_proto.sh        # 生成protobuf代码的脚本
└── README.md               # 本文件
```

## 安装依赖

在服务器上运行前，需要安装gRPC相关依赖：

```bash
pip install grpcio grpcio-tools
```

## 生成Protobuf代码

在服务器上首次使用前，需要生成protobuf的Python代码：

```bash
cd python/moonlang/srt/mooncake_core
bash generate_proto.sh
```

这会生成两个文件：
- `metadata_pb2.py` - protobuf消息定义
- `metadata_pb2_grpc.py` - gRPC服务定义

## 使用方法

### 1. 启动元数据服务器

在一个节点上启动全局元数据服务器：

```bash
python -m moonlang.srt.mooncake_core.metadata_server --port 8999
```

### 2. 配置MoonLang服务器

在启动MoonLang服务器时，添加全局缓存参数：

```bash
python -m moonlang.launch_server \
    --model-path /path/to/model \
    --enable-global-cache \
    --global-cache-metadata-server "metadata_server_ip:8999" \
    --global-cache-query-timeout 1.0 \
    --global-cache-transfer-timeout 10.0 \
    --mooncake-ib-device mlx5_0
```

### 3. 编程接口

```python
from moonlang.srt.mooncake_core import (
    MooncakeConfig,
    MooncakeTransportLayer,
    MetadataClient,
    GlobalCacheMetadataServer,
)

# 创建配置
config = MooncakeConfig(
    enable_global_cache=True,
    metadata_server_addr="10.0.0.1:8999",
    cache_query_timeout=1.0,
    transfer_timeout=10.0,
    ib_device="mlx5_0",
)

# 创建传输层
transport = MooncakeTransportLayer(config)

# 查询缓存位置
locations = transport.query_cache_location("prefix_hash_123")

# 注册本地缓存
transport.register_cache("node_1", "prefix_hash_123", [0, 1, 2, 3])

# 传输KV缓存
success = transport.transfer_kv_cache(
    session_id="session_123",
    src_addrs=[...],
    dst_addrs=[...],
    lengths=[...],
)
```

## 工作原理

1. **元数据服务器**：维护全局缓存注册表，记录哪些节点有哪些缓存前缀
2. **元数据客户端**：每个MoonLang节点通过gRPC与元数据服务器通信
3. **传输层**：复用现有的Mooncake引擎进行RDMA传输
4. **缓存查询流程**：
   - 节点收到请求时，计算prefix hash
   - 查询元数据服务器，获取缓存位置
   - 如果其他节点有缓存，通过Mooncake传输
   - 本地缓存miss时，正常执行prefill

## 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_global_cache` | bool | False | 是否启用全局缓存 |
| `global_cache_metadata_server` | str | None | 元数据服务器地址（ip:port） |
| `global_cache_query_timeout` | float | 1.0 | 查询超时时间（秒） |
| `global_cache_transfer_timeout` | float | 10.0 | 传输超时时间（秒） |
| `mooncake_ib_device` | str | None | InfiniBand设备名称 |

## 注意事项

1. **网络要求**：需要InfiniBand或RoCE网络支持
2. **依赖项**：需要安装grpcio和grpcio-tools
3. **Protobuf生成**：首次使用前必须运行generate_proto.sh
4. **元数据服务器**：建议在独立节点上运行，确保高可用性
5. **性能考虑**：元数据查询会增加少量延迟（~1ms），但可以通过本地缓存优化

## 故障排查

### 问题：ImportError: cannot import name 'metadata_pb2'

**解决方案**：运行protobuf生成脚本
```bash
cd python/moonlang/srt/mooncake_core
bash generate_proto.sh
```

### 问题：gRPC连接失败

**检查项**：
1. 元数据服务器是否运行
2. 网络连接是否正常
3. 防火墙是否开放端口

### 问题：Mooncake引擎初始化失败

**检查项**：
1. InfiniBand设备是否存在：`ibstat`
2. Mooncake库是否正确安装
3. 设备名称是否正确（如mlx5_0）

## 下一步

Phase 1完成后，接下来的工作：
- Phase 2: 实现缓存感知调度
- Phase 3: 优化传输性能
- Phase 4: 添加监控和统计
