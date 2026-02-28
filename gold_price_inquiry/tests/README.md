# 黄金价格查询工具测试

## 测试说明

本项目的测试脚本应放在此目录下。

### 需要的测试

1. **自然语言时间解析测试** - 验证各种时间格式解析是否正确
2. **Bloomberg 数据获取测试** - 测试 Bloomberg API 连接和数据获取
3. **AkShare 数据获取测试** - 测试 AkShare 备选数据源
4. **集成测试** - 测试完整的查询流程

### 运行测试

```bash
# 激活虚拟环境
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

# 安装测试依赖
pip install pytest

# 运行测试
pytest tests/
```
