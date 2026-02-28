# MoonLang

**MoonLang = SGLang + Mooncake**

MoonLang 是 SGLang 和 Mooncake 的深度集成版本，专注于提供最高性能的大语言模型推理服务。

## 项目简介

MoonLang 在 SGLang 的基础上深度集成了 Mooncake 的高性能通信和分布式 KV cache 能力，实现了：

- **全局 KV Cache 共享**: 跨节点的 RadixCache 共享，提升 cache 命中率
- **高性能通信**: 使用 Mooncake 替代 ZMQ，降低通信延迟
- **智能调度**: 网络感知的请求调度，优化跨节点通信
- **统一内存管理**: GPU-CPU-Storage 三级内存池统一管理

## 当前集成状态

SGLang 已经包含部分 Mooncake 集成：

1. **PD Disaggregation**: Prefill-Decode 分离架构使用 Mooncake 传输 KV cache
2. **MoE All-to-All**: Expert Parallelism 可以使用 Mooncake 后端
3. **HiCache Storage**: 分层缓存的存储后端支持 Mooncake

## 安装

```bash
cd python
pip install -e .
```

## 使用方式

### 启动服务器（兼容 SGLang）

```bash
# 使用 moonlang 命令（新）
python -m moonlang.launch_server --model-path meta-llama/Llama-3.1-8B-Instruct

# 或使用 sglang 命令（向后兼容）
python -m moonlang.launch_server --model-path meta-llama/Llama-3.1-8B-Instruct
```

### 启用 Mooncake 功能

```bash
# PD Disaggregation with Mooncake
python -m moonlang.launch_server \
    --model-path meta-llama/Llama-3.1-8B-Instruct \
    --disaggregation-mode prefill \
    --disaggregation-transfer-backend mooncake \
    --disaggregation-ib-device mlx5_0

# MoE with Mooncake All-to-All
python -m moonlang.launch_server \
    --model-path deepseek-ai/DeepSeek-V3 \
    --moe-a2a-backend mooncake \
    --mooncake-ib-device mlx5_0
```

## 配置参数

MoonLang 新增的 Mooncake 相关参数：

- `--disaggregation-transfer-backend mooncake`: PD 分离使用 Mooncake 传输
- `--disaggregation-ib-device`: InfiniBand 设备名称
- `--moe-a2a-backend mooncake`: MoE All-to-All 使用 Mooncake
- `--mooncake-ib-device`: Mooncake InfiniBand 设备
- `--hicache-storage-backend mooncake`: HiCache 使用 Mooncake 存储

## 开发路线图

### v0.1 (当前)
- [x] 项目重命名为 MoonLang
- [x] 保持 SGLang 向后兼容
- [x] 现有 Mooncake 集成功能可用

### v0.2 (计划中)
- [ ] 全局 RadixCache 跨节点共享
- [ ] 替换所有 ZMQ 通信为 Mooncake
- [ ] 网络感知调度器

### v1.0 (未来)
- [ ] 统一 GPU-CPU-Storage 内存管理
- [ ] 通信/计算重叠优化
- [ ] 完整的分布式 KV cache 系统

## 与 SGLang 的关系

MoonLang 是 SGLang 的增强版本，保持完全向后兼容：

- 所有 SGLang 的功能在 MoonLang 中都可用
- 可以使用 `sglang` 或 `moonlang` 命令
- 现有的 SGLang 代码无需修改即可运行

## 贡献

欢迎贡献代码！请参考 [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

Apache License 2.0 - 详见 [LICENSE](LICENSE)

## 致谢

- [SGLang](https://github.com/sgl-project/sglang) - 高性能 LLM 推理框架
- [Mooncake](https://github.com/kvcache-ai/Mooncake) - 高性能分布式 KV cache 系统
