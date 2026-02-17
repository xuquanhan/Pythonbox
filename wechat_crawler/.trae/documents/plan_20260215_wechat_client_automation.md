# 微信客户端自动化方案计划

## 1. 背景分析

### 1.1 问题现状
- 微信网页版已不再支持登录，显示"为了保障你的账号安全，暂不支持使用网页版微信"
- 服务号推送消息存储在用户聊天列表中，无法通过常规 API 获取
- 需要一种可靠的方式来获取 Wind 金融终端服务号的推送内容

### 1.2 技术选择
- **方案**：微信客户端自动化
- **原理**：使用 PyAutoGUI 和 PyWinAuto 模拟用户在微信客户端中的操作
- **优势**：
  - 直接操作微信客户端，不受网页版限制
  - 可以获取最新的推送内容
  - 操作相对简单，易于实现
  - 不需要解密数据库，避免安全风险

## 2. 技术方案

### 2.1 核心技术栈
- **PyAutoGUI**：用于模拟鼠标和键盘操作
- **PyWinAuto**：用于 Windows 应用程序自动化
- **Pillow (PIL)**：用于截图和图像处理
- **pyperclip**：用于剪贴板操作
- **pytesseract**（可选）：用于 OCR 文字识别

### 2.2 实现流程
1. **检测微信客户端状态**
   - 检查微信客户端是否已打开
   - 如果未打开，则启动微信客户端
   - 等待微信客户端完全加载

2. **定位 Wind 服务号聊天**
   - 使用快捷键 Ctrl+F 打开搜索
   - 输入 "Wind金融终端" 进行搜索
   - 点击搜索结果中的 Wind 服务号

3. **提取推送消息**
   - 滚动聊天窗口，加载更多消息
   - 使用截图或复制文本的方式提取消息内容
   - 识别消息类型（文本、图片、链接等）

4. **处理和保存内容**
   - 解析消息内容，提取关键信息
   - 保存为便于后续操作的格式（JSON/CSV/TXT）
   - 添加时间戳和服务号信息

## 3. 详细实现步骤

### 3.1 环境准备
1. 安装必要的 Python 库：
   ```bash
   pip install pyautogui pywinauto pillow pyperclip pytesseract
   ```

2. 配置 Tesseract OCR（可选）：
   - 下载并安装 Tesseract OCR
   - 配置环境变量

### 3.2 核心功能模块

#### 模块 1：微信客户端管理
```python
class WeChatClientManager:
    def __init__(self):
        self.app = None
        self.window = None
    
    def start_wechat(self):
        """启动微信客户端"""
        pass
    
    def find_wechat_window(self):
        """查找微信窗口"""
        pass
    
    def activate_wechat(self):
        """激活微信窗口"""
        pass
```

#### 模块 2：服务号定位
```python
class ServiceAccountLocator:
    def __init__(self, service_name):
        self.service_name = service_name
    
    def search_service_account(self):
        """搜索服务号"""
        pass
    
    def click_service_account(self):
        """点击服务号聊天"""
        pass
```

#### 模块 3：消息提取
```python
class MessageExtractor:
    def __init__(self):
        self.messages = []
    
    def scroll_chat_window(self):
        """滚动聊天窗口"""
        pass
    
    def extract_messages(self):
        """提取消息内容"""
        pass
    
    def save_messages(self):
        """保存消息"""
        pass
```

### 3.3 用户交互设计
- 提供简单的命令行界面
- 支持配置服务号名称和输出格式
- 提供实时日志反馈
- 支持错误处理和重试机制

## 4. 潜在问题与解决方案

### 4.1 窗口定位问题
**问题**：微信窗口位置和大小可能不固定
**解决方案**：
- 使用 PyWinAuto 精确定位窗口
- 根据窗口相对位置计算点击坐标
- 提供窗口位置校准功能

### 4.2 消息识别问题
**问题**：消息内容可能包含图片、链接等多种格式
**解决方案**：
- 优先使用复制文本的方式
- 对于图片，使用 OCR 进行识别
- 对于链接，提取 URL 并保存

### 4.3 操作延迟问题
**问题**：微信客户端响应可能有延迟
**解决方案**：
- 在关键操作后添加适当的等待时间
- 使用图像识别确认操作成功
- 提供超时处理机制

### 4.4 用户干扰问题
**问题**：自动化操作期间用户可能干扰
**解决方案**：
- 提供明确的操作提示
- 在操作期间锁定鼠标和键盘（可选）
- 提供紧急停止功能

## 5. 实施计划

### 5.1 第一阶段：基础功能实现（1-2 天）
- [ ] 安装和配置必要的库
- [ ] 实现微信客户端启动和窗口定位
- [ ] 实现服务号搜索和定位功能
- [ ] 实现基本的文本消息提取功能

### 5.2 第二阶段：功能完善（2-3 天）
- [ ] 实现消息滚动和批量提取
- [ ] 实现图片和链接消息的处理
- [ ] 实现多种输出格式支持
- [ ] 添加错误处理和重试机制

### 5.3 第三阶段：测试和优化（1-2 天）
- [ ] 进行全面功能测试
- [ ] 优化操作速度和稳定性
- [ ] 编写用户使用文档
- [ ] 提供配置选项和自定义功能

## 6. 文件结构

```
wechat_crawler/
├── modules/
│   ├── wechat_client_manager.py    # 微信客户端管理
│   ├── service_account_locator.py  # 服务号定位
│   ├── message_extractor.py        # 消息提取
│   └── wechat_client_automation.py # 整合模块
├── scripts/
│   └── wind_client_crawler.py      # Wind 服务号专用脚本
├── config/
│   └── wind_client_config.json     # 配置文件
└── data/
    └── wind/                       # 输出目录
```

## 7. 配置选项

```json
{
  "service_name": "Wind金融终端",
  "output_format": "json",
  "output_dir": "data/wind",
  "max_messages": 20,
  "scroll_times": 5,
  "wait_time": 2,
  "auto_start_wechat": true,
  "screenshot_on_error": true
}
```

## 8. 使用方式

### 8.1 基本使用
```bash
python scripts/wind_client_crawler.py
```

### 8.2 自定义配置
```bash
python scripts/wind_client_crawler.py --config config/wind_client_config.json
```

### 8.3 命令行参数
```bash
python scripts/wind_client_crawler.py --service "Wind金融终端" --output json --max 20
```

## 9. 注意事项

1. **隐私和安全**：
   - 不要在公共场合运行自动化脚本
   - 定期清理保存的消息内容
   - 不要分享敏感信息

2. **系统要求**：
   - Windows 10 或更高版本
   - Python 3.7 或更高版本
   - 微信客户端已安装并登录

3. **使用限制**：
   - 不要频繁运行，避免被微信检测
   - 操作期间不要使用鼠标和键盘
   - 确保微信窗口保持可见状态

## 10. 后续优化方向

1. **性能优化**：
   - 减少不必要的等待时间
   - 优化图像识别速度
   - 支持多线程处理

2. **功能扩展**：
   - 支持多个服务号同时处理
   - 支持定时自动运行
   - 支持消息过滤和搜索

3. **用户体验**：
   - 提供图形用户界面
   - 支持语音提示
   - 提供操作回放功能

## 11. 总结

本方案通过微信客户端自动化技术，提供了一种可靠的方式来获取 Wind 服务号的推送内容。虽然实现相对复杂，但能够有效解决微信网页版不可用的问题，为用户提供稳定的内容获取服务。

实施过程中需要注意：
1. 确保微信客户端正常运行
2. 遵循微信使用规范，避免频繁操作
3. 保护用户隐私和数据安全
4. 提供良好的用户体验和错误处理

通过本方案的实施，用户将能够方便地获取 Wind 服务号的定制新闻，用于后续的其他操作。
