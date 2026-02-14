## 功能需求

1. 读取已保存的公众号监控列表
2. 显示现有列表并询问是否添加新公众号
3. 支持一次性添加多个公众号（逗号分隔）
4. 自动登录微信公众号后台（扫码）
5. 自动获取token、cookie、fakeid
6. 爬取所有监控公众号的文章
7. 保存数据并更新监控列表

## 实现步骤

### 1. 安装依赖

* selenium-wire（拦截浏览器请求）

* 其他必要依赖

### 2. 创建配置文件

* wechat\_accounts.json（存储监控的公众号列表）

* wechat\_session.json（存储登录会话信息）

### 3. 创建自动登录模块

* wechat\_auto\_login.py

* 实现扫码登录

* 自动提取token和cookie

* 自动搜索公众号获取fakeid

### 4. 创建API爬虫模块

* wechat\_api\_crawler.py

* 使用微信公众号后台API获取文章

* 实现翻页获取历史文章

### 5. 修改主程序

* 读取监控列表

* 显示并询问添加新公众号

* 调用自动登录和爬虫模块

* 保存更新后的列表

### 6. 数据存储优化

* 保存文章到数据库

* 去重处理

* 导出功能

## 文件结构

```
wechat_crawler/
├── modules/
│   ├── crawler.py（原有）
│   ├── wechat_auto_login.py（新建）
│   ├── wechat_api_crawler.py（新建）
│   └── storage.py（原有）
├── config/
│   ├── wechat_accounts.json（公众号监控列表）
│   └── wechat_session.json（登录会话）
├── scripts/
│   └── main.py（修改）
└── requirements.txt（更新）
```

## 使用流程

```
运行脚本
    ↓
读取wechat_accounts.json
    ↓
显示现有监控列表
    ↓
询问：是否添加新公众号？（Y/N）
    ↓
如果Y：输入公众号名称（支持逗号分隔多个）
    ↓
添加到监控列表
    ↓
检查是否需要登录（无有效session或已过期）
    ↓
如果需要：打开浏览器，显示二维码，用户扫码
    ↓
自动获取token、cookie
    ↓
遍历监控列表中的每个公众号
    ↓
搜索公众号获取fakeid
    ↓
调用API获取文章列表
    ↓
保存文章到数据库
    ↓
导出数据
```

## 预期效果

* 全自动运行，只需首次扫码登录

* 支持多公众号监控

* 数据自动保存和去重

* 会话过期自动重新登录

