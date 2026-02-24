# EPUB转Mobi翻译工具

一个基于浏览器的Web工具，用于将EPUB电子书转换为Mobi格式，并支持使用阿里Qwen大语言模型进行翻译。

## 功能特性

- 📄 **EPUB解析** - 读取并解析EPUB文件结构和内容
- 🔄 **格式转换** - 将EPUB转换为Mobi格式（Kindle兼容）
- 🌐 **智能翻译** - 使用阿里Qwen大语言模型将非中文材料翻译成中文
- 📊 **进度显示** - 实时显示处理进度

## 项目结构

```
epub_converter/
├── .streamlit/
│   └── config.toml              # Streamlit配置文件
├── tools/
│   ├── epub_parser.py           # EPUB解析模块
│   ├── converter.py             # 格式转换模块
│   └── translator.py            # 翻译模块
├── .env.example                # 环境变量配置示例
├── app.py                      # Streamlit Web应用主程序
└── requirements.txt            # 依赖包列表
```

## 环境配置

### 1. 安装依赖

```bash
cd c:/Dev/PythonBox/epub_converter
pip install -r requirements.txt
```

### 2. 配置API密钥

复制 `.env.example` 为 `.env`，填入你的阿里DashScope API密钥：

```bash
# 阿里Qwen (DashScope)
DASHSCOPE_API_KEY_QWEN=your-dashscope-api-key
```

获取API密钥：https://dashscope.console.aliyun.com/

## 启动方式

```bash
cd c:/Dev/PythonBox/epub_converter
python -m streamlit run app.py --server.port 8502
```

## 访问地址

🌐 **http://localhost:8502**

## 使用说明

1. **上传EPUB文件** - 选择要处理的电子书
2. **选择操作** - 转换格式、翻译或两者同时进行
3. **配置选项** - 选择源语言和目标语言
4. **开始处理** - 点击按钮进行处理

### 操作类型

- **仅转换格式** - 将EPUB转换为Mobi格式，不进行翻译
- **仅翻译** - 仅对EPUB内容进行翻译，保持EPUB格式
- **翻译后转换** - 先翻译再转换为Mobi格式

### 语言选项

- 源语言：自动检测、英语、日语、韩语、法语、德语、西班牙语
- 目标语言：中文、英语、日语

## 依赖说明

| 依赖包 | 说明 |
|--------|------|
| streamlit | Web界面框架 |
| ebooklib | EPUB文件处理 |
| dashscope | 阿里Qwen API调用 |
| python-dotenv | 环境变量管理 |
| lxml | XML解析 |

## 注意事项

- 翻译功能需要配置 `DASHSCOPE_API_KEY_QWEN` 环境变量
- Mobipocket转换功能需要安装KindleGen（可选）
- 大文件翻译可能需要较长时间，请耐心等待

## 版本

v1.0.0
