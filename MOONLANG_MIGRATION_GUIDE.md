# MoonLang 迁移指南

## 阶段1: 重命名和品牌更新 (当前阶段)

### 步骤1: 更新项目配置文件

```bash
# 1.1 更新 pyproject.toml
cd python
```

**需要修改的文件:**
- `python/pyproject.toml` - 项目名称和描述
- `python/sglang/__init__.py` - 包名和导入
- `python/sglang/version.py` - 版本信息
- `README.md` - 项目介绍
- `docs/` - 所有文档

### 步骤2: 批量重命名

```bash
# 创建重命名脚本
cat > rename_to_moonlang.sh << 'EOF'
#!/bin/bash
set -e

echo "=== MoonLang 重命名脚本 ==="

# 1. 重命名主目录
echo "重命名 python/sglang -> python/moonlang"
mv python/sglang python/moonlang

# 2. 更新所有Python文件中的导入
echo "更新Python导入语句..."
find python/moonlang -type f -name "*.py" -exec sed -i '' 's/from sglang/from moonlang/g' {} +
find python/moonlang -type f -name "*.py" -exec sed -i '' 's/import sglang/import moonlang/g' {} +

# 3. 更新测试文件
echo "更新测试文件..."
find test -type f -name "*.py" -exec sed -i '' 's/from sglang/from moonlang/g' {} +
find test -type f -name "*.py" -exec sed -i '' 's/import sglang/import moonlang/g' {} +

# 4. 更新示例文件
echo "更新示例文件..."
find examples -type f -name "*.py" -exec sed -i '' 's/from sglang/from moonlang/g' {} +
find examples -type f -name "*.py" -exec sed -i '' 's/import sglang/import moonlang/g' {} +

# 5. 更新benchmark文件
echo "更新benchmark文件..."
find benchmark -type f -name "*.py" -exec sed -i '' 's/from sglang/from moonlang/g' {} +
find benchmark -type f -name "*.py" -exec sed -i '' 's/import sglang/import moonlang/g' {} +

echo "=== 重命名完成 ==="
EOF

chmod +x rename_to_moonlang.sh
```

### 步骤3: 更新配置文件

创建以下文件来更新配置：

```bash
# update_configs.sh
cat > update_configs.sh << 'EOF'
#!/bin/bash

# 更新 pyproject.toml
sed -i '' 's/name = "sglang"/name = "moonlang"/g' python/pyproject.toml
sed -i '' 's/SGLang is a fast/MoonLang is a fast/g' python/pyproject.toml
sed -i '' 's/sglang = "sglang.cli.main:main"/moonlang = "moonlang.cli.main:main"/g' python/pyproject.toml

# 更新 README.md
sed -i '' 's/SGLang/MoonLang/g' README.md
sed -i '' 's/sglang/moonlang/g' README.md

echo "配置文件更新完成"
EOF

chmod +x update_configs.sh
```

## 阶段2: 添加Mooncake集成

### 步骤4: 添加Mooncake作为依赖

```bash
# 在 python/pyproject.toml 的 dependencies 中添加
"mooncake-transfer-engine>=0.3.9",
```

### 步骤5: 创建Mooncake传输层

创建新的目录结构：

```bash
mkdir -p python/moonlang/srt/transport
touch python/moonlang/srt/transport/__init__.py
```

### 步骤6: 创建核心集成文件

这些文件将在后续步骤中创建。

## 阶段3: 前端开发

### 步骤7: 初始化前端项目

```bash
# 创建前端目录
mkdir -p frontend
cd frontend

# 初始化React项目
npm create vite@latest . -- --template react-ts

# 安装依赖
npm install
npm install -D tailwindcss postcss autoprefixer
npm install recharts lucide-react
npm install @tanstack/react-query axios

# 初始化Tailwind
npx tailwindcss init -p
```

## 阶段4: 测试和验证

### 步骤8: 运行测试

```bash
# 安装开发依赖
cd python
pip install -e ".[dev]"

# 运行测试
pytest moonlang/test/ -v

# 验证导入
python -c "import moonlang; print(moonlang.__version__)"
```

## 阶段5: 文档更新

### 步骤9: 更新所有文档

- 更新 docs/ 目录下的所有文档
- 更新 README.md
- 创建 MIGRATION.md 指导用户从SGLang迁移

## 检查清单

- [ ] 重命名 python/sglang -> python/moonlang
- [ ] 更新所有导入语句
- [ ] 更新 pyproject.toml
- [ ] 更新 README.md
- [ ] 添加 Mooncake 依赖
- [ ] 创建 transport 层
- [ ] 初始化前端项目
- [ ] 运行测试验证
- [ ] 更新文档
- [ ] 提交到Git

## 下一步

完成这些步骤后，继续执行详细的集成计划。
