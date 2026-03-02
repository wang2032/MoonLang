# MoonLang Phase 1 进度报告

## 概述

Phase 1的目标是实现MoonLang的全局KV缓存共享基础设施，包括：
1. gRPC元数据服务（用于跨节点缓存协调）
2. Mooncake传输层（复用现有实现）
3. Scheduler集成（初始化和辅助方法）

## 完成情况

### ✅ Phase 1.1: gRPC通信层实现

**完成时间**: 2026-03-02

**创建的文件**:
- `python/moonlang/srt/mooncake_core/metadata.proto` - Protobuf定义
- `python/moonlang/srt/mooncake_core/metadata_server.py` - 元数据服务器（gRPC）
- `python/moonlang/srt/mooncake_core/metadata_client.py` - 元数据客户端（gRPC）
- `python/moonlang/srt/mooncake_core/generate_proto.sh` - Protobuf代码生成脚本
- `python/moonlang/srt/mooncake_core/test_grpc.py` - gRPC通信测试脚本
- `python/moonlang/srt/mooncake_core/README.md` - 模块使用文档

**功能**:
- ✅ 定义了3个RPC服务：QueryCache, RegisterCache, UpdateNodeStatus
- ✅ 实现了gRPC服务器（MetadataServicer）
- ✅ 实现了gRPC客户端（带本地缓存）
- ✅ 支持多节点缓存注册和查询
- ✅ 提供完整的测试脚本

**测试方法**:
```bash
# 1. 生成protobuf代码
cd python/moonlang/srt/mooncake_core
bash generate_proto.sh

# 2. 启动测试服务器
python test_grpc.py --mode server --port 8999

# 3. 运行客户端测试
python test_grpc.py --mode client --server localhost:8999
```

### ✅ Phase 1.2: Scheduler集成

**完成时间**: 2026-03-02

**修改的文件**:
- `python/moonlang/srt/managers/scheduler.py` - 添加Mooncake初始化和辅助方法

**新增方法**:
1. `init_mooncake_transport()` - 初始化Mooncake传输层
   - 创建MooncakeConfig
   - 初始化MooncakeTransportLayer
   - 生成节点ID
   - 验证连接状态

2. `compute_prefix_hash(input_ids)` - 计算缓存前缀哈希
   - 使用前128个token作为前缀
   - SHA256哈希，取前16字符

3. `query_global_cache(prefix_hash)` - 查询全局缓存
   - 调用MooncakeTransportLayer.query_cache_location()
   - 返回缓存位置列表

4. `register_cache_to_global(prefix_hash, kv_indices)` - 注册本地缓存
   - 调用MooncakeTransportLayer.register_cache()
   - 向元数据服务器注册

5. `fetch_remote_cache(...)` - 获取远程缓存
   - 占位符方法，Phase 2实现

**集成点**:
- 在`Scheduler.__init__()`中调用`init_mooncake_transport()`
- 位置：在`init_cache_with_memory_pool()`之后
- 仅在主scheduler rank (tp_rank=0, pp_rank=0)上初始化

**测试方法**:
```bash
python -m moonlang.srt.mooncake_core.test_scheduler_integration
```

### 📝 Phase 1.3: 待完成

**下一步工作**:
1. 在请求处理流程中添加缓存查询逻辑
   - 修改`handle_generate_request()`方法
   - 在prefill前查询全局缓存
   - 如果命中，尝试从远程获取

2. 在缓存插入时注册到全局
   - 修改RadixCache的insert逻辑
   - 在本地缓存后注册到元数据服务器

3. 添加配置验证
   - 检查InfiniBand设备
   - 验证元数据服务器连接

## 架构设计

### 组件关系

```
┌─────────────────────────────────────────────────────────────┐
│                    Metadata Server                          │
│                  (GlobalCacheMetadataServer)                │
│                                                             │
│  - Cache Registry: prefix_hash -> [node_locations]         │
│  - Node Registry: node_id -> node_status                   │
│  - gRPC Service: QueryCache, RegisterCache, UpdateStatus   │
└──────────────────────┬──────────────────────────────────────┘
                       │ gRPC
          ┌────────────┴────────────┐
          │                         │
┌─────────▼─────────┐    ┌─────────▼─────────┐
│   Scheduler 1     │    │   Scheduler 2     │
│                   │    │                   │
│ MooncakeTransport │    │ MooncakeTransport │
│   - MetadataClient│    │   - MetadataClient│
│   - TransferEngine│◄───┼───►TransferEngine│
│                   │    │                   │
│ RadixCache        │    │ RadixCache        │
└───────────────────┘    └───────────────────┘
         │                        │
         │   Mooncake/RDMA       │
         └────────────────────────┘
```

### 数据流

1. **缓存注册流程**:
   ```
   Scheduler.handle_request()
     → RadixCache.insert()
     → Scheduler.register_cache_to_global()
     → MooncakeTransportLayer.register_cache()
     → MetadataClient.register_cache()
     → [gRPC] → MetadataServer.RegisterCache()
   ```

2. **缓存查询流程**:
   ```
   Scheduler.handle_request()
     → Scheduler.compute_prefix_hash()
     → Scheduler.query_global_cache()
     → MooncakeTransportLayer.query_cache_location()
     → MetadataClient.query_cache()
     → [gRPC] → MetadataServer.QueryCache()
     → 返回: [(node_id, kv_indices), ...]
   ```

3. **缓存传输流程** (Phase 2):
   ```
   Scheduler.fetch_remote_cache()
     → MooncakeTransportLayer.transfer_kv_cache()
     → Mooncake Engine (batch_transfer_sync)
     → [RDMA] → Remote Node
   ```

## 配置参数

### ServerArgs新增参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_global_cache` | bool | False | 启用全局KV缓存共享 |
| `global_cache_metadata_server` | str | None | 元数据服务器地址（ip:port） |
| `global_cache_query_timeout` | float | 1.0 | 查询超时（秒） |
| `global_cache_transfer_timeout` | float | 10.0 | 传输超时（秒） |

### 使用示例

```bash
python -m moonlang.launch_server \
    --model-path Qwen/Qwen2.5-3B-Instruct \
    --enable-global-cache \
    --global-cache-metadata-server "10.0.0.1:8999" \
    --global-cache-query-timeout 1.0 \
    --global-cache-transfer-timeout 10.0 \
    --mooncake-ib-device mlx5_0
```

## 测试覆盖

### 单元测试

1. **gRPC通信测试** (`test_grpc.py`)
   - ✅ 服务器启动
   - ✅ 客户端连接
   - ✅ 缓存注册
   - ✅ 缓存查询
   - ✅ 节点状态更新
   - ✅ 本地缓存TTL
   - ✅ 多节点场景

2. **Scheduler集成测试** (`test_scheduler_integration.py`)
   - ✅ ServerArgs配置
   - ✅ MooncakeConfig验证
   - ✅ MooncakeTransportLayer初始化
   - ✅ 前缀哈希计算
   - ✅ 哈希确定性验证

### 集成测试（待完成）

- [ ] 端到端缓存共享测试
- [ ] 多节点并发测试
- [ ] 故障恢复测试
- [ ] 性能基准测试

## 性能考虑

### 延迟分析

1. **元数据查询延迟**: ~1ms
   - gRPC往返时间
   - 本地缓存可减少到 <0.1ms

2. **缓存传输延迟**: ~5-10ms (取决于缓存大小)
   - RDMA传输时间
   - 网络带宽限制

3. **总体影响**: 
   - 缓存命中：节省prefill时间（可能数百ms到数秒）
   - 缓存未命中：增加1ms查询延迟（可接受）

### 优化策略

1. **本地缓存**: MetadataClient使用60秒TTL
2. **批量注册**: 可以批量注册多个缓存前缀
3. **异步查询**: 查询可以与其他操作并行
4. **预取**: 可以预测性地预取热门缓存

## 依赖项

### Python包
- `grpcio` >= 1.50.0
- `grpcio-tools` >= 1.50.0
- `protobuf` >= 3.20.0

### 系统要求
- InfiniBand或RoCE网络
- Mooncake库（已包含在MoonLang中）

### 安装命令
```bash
pip install grpcio grpcio-tools protobuf
```

## 文档

- [模块README](python/moonlang/srt/mooncake_core/README.md) - 详细使用说明
- [部署指南](MOONLANG_PHASE1_DEPLOYMENT.md) - 完整部署步骤
- [迁移指南](MOONLANG_MIGRATION_GUIDE.md) - 从SGLang迁移

## 下一步计划

### Phase 1.3: 请求处理集成（预计1-2天）

1. 修改`handle_generate_request()`
   - 添加缓存查询逻辑
   - 实现缓存命中处理

2. 修改RadixCache
   - 添加全局注册回调
   - 在insert时触发注册

3. 添加监控指标
   - 缓存命中率
   - 查询延迟
   - 传输时间

### Phase 2: 远程缓存传输（预计3-5天）

1. 实现`fetch_remote_cache()`
   - 协调远程节点地址
   - 调用Mooncake传输

2. 添加缓存感知调度
   - 优先调度到有缓存的节点
   - 负载均衡考虑

3. 性能优化
   - 批量传输
   - 并行传输多层

### Phase 3: 监控和可视化（预计2-3天）

1. 添加Prometheus指标
2. 创建Grafana仪表板
3. 添加日志分析工具

## 已知问题

1. **Mooncake引擎依赖**: 需要InfiniBand硬件
   - 解决方案：提供模拟模式用于测试

2. **gRPC连接管理**: 长时间运行可能需要重连
   - 解决方案：添加心跳和自动重连

3. **元数据服务器单点**: 元数据服务器故障会影响全局缓存
   - 解决方案：Phase 3添加高可用支持

## 贡献者

- 主要开发：Phase 1实现
- 代码审查：待定
- 测试：待定

## 更新日志

### 2026-03-02
- ✅ 完成Phase 1.1: gRPC通信层
- ✅ 完成Phase 1.2: Scheduler集成
- 📝 创建进度报告文档

---

**状态**: Phase 1.2 完成，Phase 1.3 进行中
**完成度**: 约70%
**预计完成时间**: 2026-03-05
