# MoonLang Phase 1 部署指南

本文档说明如何部署和测试MoonLang Phase 1的全局KV缓存功能。

## 前置条件

### 硬件要求
- 多个GPU节点（至少2个）
- InfiniBand或RoCE网络连接
- 每个节点至少16GB GPU内存

### 软件要求
- Python 3.10+
- CUDA 12.0+
- PyTorch 2.0+
- gRPC库

## 安装步骤

### 1. 安装MoonLang

```bash
cd python
pip install -e .
```

### 2. 安装gRPC依赖

```bash
pip install grpcio grpcio-tools
```

### 3. 生成Protobuf代码

```bash
cd python/moonlang/srt/mooncake_core
bash generate_proto.sh
```

验证生成成功：
```bash
ls -la metadata_pb2.py metadata_pb2_grpc.py
```

## 部署架构

```
┌─────────────────────┐
│  Metadata Server    │  <- 独立节点或其中一个GPU节点
│  (Port 8999)        │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼────┐   ┌───▼────┐
│ Node 1 │   │ Node 2 │  <- GPU节点运行MoonLang
│ GPU 0  │   │ GPU 0  │
└────────┘   └────────┘
```

## 部署步骤

### 步骤1：启动元数据服务器

在一个节点上（可以是GPU节点或独立节点）：

```bash
# 方法1：使用测试脚本
python -m moonlang.srt.mooncake_core.test_grpc --mode server --port 8999

# 方法2：使用主程序
python -m moonlang.srt.mooncake_core.metadata_server --port 8999 --log-level INFO
```

验证服务器运行：
```bash
# 在另一个终端
netstat -tuln | grep 8999
```

### 步骤2：测试gRPC通信

在另一个终端测试客户端连接：

```bash
python -m moonlang.srt.mooncake_core.test_grpc \
    --mode client \
    --server <metadata_server_ip>:8999
```

预期输出：
```
[2026-03-02 10:00:00] INFO: Connecting to metadata server at localhost:8999
[2026-03-02 10:00:00] INFO: Test 1: Register cache
[2026-03-02 10:00:00] INFO: Register cache result: True
[2026-03-02 10:00:00] INFO: Test 2: Query cache
[2026-03-02 10:00:00] INFO: Query cache result: [{'node_id': 'node_1', ...}]
...
[2026-03-02 10:00:01] INFO: All tests completed successfully!
```

### 步骤3：启动MoonLang节点（Node 1）

```bash
# 设置环境变量
export METADATA_SERVER="<metadata_server_ip>:8999"
export IB_DEVICE="mlx5_0"  # 根据实际设备调整

# 启动MoonLang服务器
python -m moonlang.launch_server \
    --model-path Qwen/Qwen2.5-3B-Instruct \
    --host 0.0.0.0 \
    --port 30000 \
    --enable-global-cache \
    --global-cache-metadata-server $METADATA_SERVER \
    --global-cache-query-timeout 1.0 \
    --global-cache-transfer-timeout 10.0 \
    --mooncake-ib-device $IB_DEVICE
```

### 步骤4：启动MoonLang节点（Node 2）

在第二个GPU节点上：

```bash
# 设置环境变量
export METADATA_SERVER="<metadata_server_ip>:8999"
export IB_DEVICE="mlx5_0"

# 启动MoonLang服务器
python -m moonlang.launch_server \
    --model-path Qwen/Qwen2.5-3B-Instruct \
    --host 0.0.0.0 \
    --port 30000 \
    --enable-global-cache \
    --global-cache-metadata-server $METADATA_SERVER \
    --global-cache-query-timeout 1.0 \
    --global-cache-transfer-timeout 10.0 \
    --mooncake-ib-device $IB_DEVICE
```

## 验证部署

### 1. 检查元数据服务器

```bash
# 查看服务器日志，应该看到节点注册信息
# 日志示例：
# [2026-03-02 10:05:00] INFO: Registered cache: node=node_1, prefix=abc123, indices=5
```

### 2. 测试缓存共享

发送相同的请求到两个节点：

```bash
# 请求1 -> Node 1（会执行prefill并缓存）
curl http://node1:30000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-3B-Instruct",
    "prompt": "What is artificial intelligence?",
    "max_tokens": 100
  }'

# 请求2 -> Node 2（应该从Node 1获取缓存）
curl http://node2:30000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-3B-Instruct",
    "prompt": "What is artificial intelligence?",
    "max_tokens": 100
  }'
```

### 3. 查看性能指标

观察日志中的缓存命中率和传输时间：

```bash
# Node 2的日志应该显示：
# [2026-03-02 10:06:00] INFO: Cache hit from remote node: node_1
# [2026-03-02 10:06:00] INFO: KV cache transfer completed in 5.2ms
```

## 故障排查

### 问题1：protobuf导入错误

```
ImportError: cannot import name 'metadata_pb2'
```

**解决方案**：
```bash
cd python/moonlang/srt/mooncake_core
bash generate_proto.sh
```

### 问题2：gRPC连接失败

```
grpc.RpcError: failed to connect to all addresses
```

**检查项**：
1. 元数据服务器是否运行：`netstat -tuln | grep 8999`
2. 防火墙是否开放端口：`sudo firewall-cmd --add-port=8999/tcp`
3. 网络连接是否正常：`ping <metadata_server_ip>`

### 问题3：Mooncake引擎初始化失败

```
Failed to initialize Mooncake engine
```

**检查项**：
1. InfiniBand设备是否存在：
   ```bash
   ibstat
   # 或
   ls /sys/class/infiniband/
   ```

2. 设备名称是否正确：
   ```bash
   # 查看可用设备
   ibstat | grep "CA '"
   # 输出示例：CA 'mlx5_0'
   ```

3. Mooncake库是否安装：
   ```bash
   python -c "from moonlang.srt.distributed.parallel_state import get_mooncake_transfer_engine; print('OK')"
   ```

### 问题4：CUDA内存不足

```
RuntimeError: CUDA out of memory
```

**解决方案**：
- 减少`--max-total-tokens`
- 使用更小的模型
- 增加`--mem-fraction-static`

## 性能调优

### 1. 元数据服务器

```bash
# 增加工作线程数（修改metadata_server.py）
self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
```

### 2. 缓存查询超时

```bash
# 减少超时时间以降低延迟
--global-cache-query-timeout 0.5
```

### 3. 本地缓存TTL

修改`metadata_client.py`：
```python
self.cache_ttl = 30.0  # 从60秒减少到30秒
```

## 监控和日志

### 查看元数据服务器统计

在元数据服务器节点：
```python
from moonlang.srt.mooncake_core.metadata_server import GlobalCacheMetadataServer

# 假设服务器实例为server
stats = server.get_statistics()
print(f"Total cache entries: {stats['total_cache_entries']}")
print(f"Total nodes: {stats['total_nodes']}")
print(f"Total queries: {stats['total_queries']}")
```

### 启用详细日志

```bash
# 启动时添加日志级别
python -m moonlang.launch_server \
    --log-level debug \
    ...
```

## 下一步

Phase 1完成后，继续：
1. ~~**Phase 1.1**：实现gRPC通信层~~ ✅ 已完成
2. ~~**Phase 1.2**：集成到Scheduler~~ ✅ 已完成
3. **Phase 1.3**：添加缓存查询逻辑到请求处理流程
4. **Phase 2**：实现缓存感知调度和远程缓存传输
5. **Phase 3**：优化传输性能，添加批量传输
6. **Phase 4**：添加监控指标和可视化

## Phase 1.2 完成情况

### 已完成
- ✅ 在Scheduler中添加`init_mooncake_transport()`方法
- ✅ 在Scheduler.__init__中调用Mooncake初始化
- ✅ 添加缓存辅助方法：
  - `compute_prefix_hash()` - 计算缓存前缀哈希
  - `query_global_cache()` - 查询全局缓存
  - `register_cache_to_global()` - 注册本地缓存
  - `fetch_remote_cache()` - 获取远程缓存（占位符）
- ✅ 创建集成测试脚本

### 测试Scheduler集成

```bash
# 测试Scheduler集成（不需要实际运行服务器）
python -m moonlang.srt.mooncake_core.test_scheduler_integration
```

预期输出：
```
[2026-03-02 10:00:00] INFO: Testing Scheduler integration with Mooncake transport layer
[2026-03-02 10:00:00] INFO: Test 1: Scheduler initialization with global cache disabled
[2026-03-02 10:00:00] INFO: ✓ ServerArgs created with enable_global_cache=False
...
[2026-03-02 10:00:01] INFO: ✓ All integration tests passed!
```

## 参考资料

- [MoonLang迁移指南](MOONLANG_MIGRATION_GUIDE.md)
- [MoonLang快速开始](QUICKSTART_MOONLANG.md)
- [Mooncake Core README](python/moonlang/srt/mooncake_core/README.md)
