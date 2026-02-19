#!/usr/bin/env python3
"""
Wind服务号消息获取脚本（使用uiautomation）
通过微信PC版获取Wind服务号推送的消息
支持定时自动获取
"""

import os
import sys
import json
import time
import logging
import signal
import subprocess
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/wind_message.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

CONFIG_FILE = 'config/wind_message_config.json'
OUTPUT_DIR = 'data/wind_messages'


def load_config() -> Dict:
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
    return get_default_config()


def get_default_config() -> Dict:
    """获取默认配置"""
    return {
        'service_name': 'Wind金融终端',
        'output_format': 'json',
        'output_dir': OUTPUT_DIR,
        'max_messages': 50,
        'auto_run': False,
        'run_interval': 300,
        'last_message_id': ''
    }


def save_config(config: Dict):
    """保存配置文件"""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info("配置文件已保存")
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")


def check_uiautomation_installed() -> bool:
    """检查uiautomation是否已安装"""
    try:
        import uiautomation
        return True
    except ImportError:
        return False


def install_uiautomation():
    """安装uiautomation库"""
    print("正在安装 uiautomation 库...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'uiautomation'])
        return True
    except Exception as e:
        print(f"安装uiautomation失败: {e}")
        return False


def ensure_uiautomation():
    """确保uiautomation已安装"""
    if check_uiautomation_installed():
        return True

    print("uiautomation 未安装，正在安装...")
    if install_uiautomation():
        if check_uiautomation_installed():
            print("uiautomation 安装成功!")
            return True
    return False


def check_wechat_running() -> bool:
    """检查微信是否正在运行"""
    try:
        import uiautomation as auto
        # 尝试多种可能的窗口名称
        possible_names = ["微信", "WeChat", "Weixin"]
        for name in possible_names:
            wechat = auto.WindowControl(Name=name)
            if wechat.Exists(0.5):
                logger.info(f"找到微信窗口: {name}")
                return True
        # 也尝试按类名查找
        wechat = auto.WindowControl(ClassName="WeChatMainWndForPC")
        if wechat.Exists(0.5):
            logger.info("找到微信窗口(按类名)")
            return True
        return False
    except Exception as e:
        logger.warning(f"检查微信运行状态出错: {e}")
        return False


def start_wechat() -> bool:
    """启动微信"""
    try:
        wechat_paths = [
            r"C:\Program Files\Tencent\WeChat\WeChat.exe",
            r"C:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
        ]
        for path in wechat_paths:
            if os.path.exists(path):
                subprocess.Popen(path)
                logger.info(f"已启动微信: {path}")
                time.sleep(5)
                return True
        return False
    except Exception as e:
        logger.error(f"启动微信失败: {e}")
        return False


class WindMessageGetter:
    """Wind服务号消息获取器"""

    def __init__(self, config: Dict = None):
        self.config = config or load_config()
        self.service_name = self.config.get('service_name', 'Wind金融终端')
        self.output_format = self.config.get('output_format', 'json')
        self.output_dir = self.config.get('output_dir', OUTPUT_DIR)
        self.max_messages = self.config.get('max_messages', 50)
        self.last_message_id = self.config.get('last_message_id', '')

        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Wind消息获取器初始化完成, 服务号: {self.service_name}")

    def connect_wechat(self) -> bool:
        """连接微信"""
        try:
            if not check_uiautomation_installed():
                logger.error("uiautomation 未安装")
                return False

            import uiautomation as auto

            if not check_wechat_running():
                logger.info("微信未运行，尝试启动...")
                if not start_wechat():
                    logger.error("无法启动微信")
                    return False
                logger.info("等待微信启动...")
                time.sleep(8)

            logger.info("正在连接微信...")
            # 尝试多种方式查找微信窗口
            possible_names = ["微信", "WeChat", "Weixin"]
            for name in possible_names:
                self.wechat = auto.WindowControl(Name=name)
                if self.wechat.Exists(2):
                    logger.info(f"微信连接成功: {name}")
                    return True
            
            # 尝试按类名查找
            self.wechat = auto.WindowControl(ClassName="WeChatMainWndForPC")
            if self.wechat.Exists(2):
                logger.info("微信连接成功(按类名)")
                return True
            
            logger.error("找不到微信窗口")
            return False

        except Exception as e:
            logger.error(f"连接微信失败: {e}")
            return False

    def get_service_account_chat(self):
        """获取服务号聊天 - 使用搜索方式"""
        try:
            if not hasattr(self, 'wechat') or not self.wechat:
                return None

            logger.info(f"正在查找服务号: {self.service_name}")

            # 激活微信窗口
            self.wechat.SetActive()
            time.sleep(0.5)
            
            # 使用Ctrl+F打开搜索
            import uiautomation as auto
            
            # 发送Ctrl+F搜索
            auto.SendKeys('{Ctrl}f', waitTime=0.5)
            time.sleep(1)
            
            # 输入服务号名称
            auto.SendKeys(self.service_name, waitTime=0.3)
            time.sleep(1)
            
            # 按回车选择第一个结果
            auto.SendKeys('{Enter}', waitTime=0.5)
            time.sleep(1)
            
            logger.info(f"已搜索并选择: {self.service_name}")
            return True

        except Exception as e:
            logger.error(f"查找服务号失败: {e}")
            return None

    def get_messages(self, chat_item) -> List[Dict]:
        """获取聊天消息 - 使用剪贴板"""
        messages = []
        try:
            if not chat_item:
                return messages

            import uiautomation as auto
            
            # 确保微信窗口激活
            self.wechat.SetActive()
            time.sleep(0.5)
            
            # 使用Ctrl+A选择所有消息，然后Ctrl+C复制
            logger.info("正在复制聊天内容...")
            
            # 点击聊天区域确保焦点正确
            auto.SendKeys('{Click}', waitTime=0.3)
            time.sleep(0.3)
            
            # 全选并复制
            auto.SendKeys('{Ctrl}a', waitTime=0.3)
            time.sleep(0.3)
            auto.SendKeys('{Ctrl}c', waitTime=0.5)
            time.sleep(0.5)
            
            # 从剪贴板获取内容
            import pyperclip
            try:
                clipboard_content = pyperclip.paste()
                logger.info(f"从剪贴板获取到 {len(clipboard_content)} 字符")
                
                if clipboard_content:
                    # 按行分割消息
                    lines = clipboard_content.split('\n')
                    for i, line in enumerate(lines[:self.max_messages]):
                        line = line.strip()
                        if line and len(line) > 1:
                            msg_id = f"{line[:30]}_{time.time()}"
                            message_dict = {
                                'id': msg_id,
                                'type': 'text',
                                'content': line,
                                'sender': self.service_name,
                                'service_name': self.service_name,
                                'crawl_time': datetime.now().isoformat()
                            }
                            messages.append(message_dict)
                
            except Exception as e:
                logger.warning(f"读取剪贴板失败: {e}")

        except Exception as e:
            logger.error(f"获取消息失败: {e}")

        return messages

    def save_messages(self, messages: List[Dict]) -> List[str]:
        """保存消息到文件"""
        saved_files = []
        if not messages:
            return saved_files

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            if self.output_format == 'json':
                filepath = os.path.join(self.output_dir, f'wind_messages_{timestamp}.json')
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump({
                        'service_name': self.service_name,
                        'message_count': len(messages),
                        'crawl_time': datetime.now().isoformat(),
                        'messages': messages
                    }, f, ensure_ascii=False, indent=2)
                saved_files.append(filepath)
                logger.info(f"JSON文件已保存: {filepath}")

            elif self.output_format == 'txt':
                filepath = os.path.join(self.output_dir, f'wind_messages_{timestamp}.txt')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Wind服务号消息\n")
                    f.write(f"服务号: {self.service_name}\n")
                    f.write(f"消息数量: {len(messages)}\n")
                    f.write(f"获取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n\n")

                    for i, msg in enumerate(messages, 1):
                        f.write(f"【消息 {i}】\n")
                        f.write(f"内容: {msg.get('content')}\n")
                        f.write(f"爬取时间: {msg.get('crawl_time')}\n")
                        f.write("-" * 40 + "\n")
                saved_files.append(filepath)
                logger.info(f"TXT文件已保存: {filepath}")

            elif self.output_format == 'csv':
                import pandas as pd
                filepath = os.path.join(self.output_dir, 'wind_messages.csv')
                df = pd.DataFrame(messages)
                if os.path.exists(filepath):
                    df_existing = pd.read_csv(filepath, encoding='utf-8-sig')
                    df = pd.concat([df_existing, df], ignore_index=True)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                saved_files.append(filepath)
                logger.info(f"CSV文件已保存: {filepath}")

            if messages:
                self.config['last_message_id'] = messages[-1].get('id', '')
                save_config(self.config)

        except Exception as e:
            logger.error(f"保存消息失败: {e}")

        return saved_files

    def run(self) -> List[str]:
        """运行获取任务"""
        logger.info("=" * 60)
        logger.info("开始获取Wind服务号消息")
        logger.info("=" * 60)

        if not self.connect_wechat():
            logger.error("无法连接微信")
            return []

        if not self.get_service_account_chat():
            logger.error("未找到Wind服务号聊天")
            return []

        messages = self.get_messages(True)
        if not messages:
            logger.warning("未获取到任何消息")
            return []

        if self.last_message_id:
            new_messages = []
            for msg in messages:
                if msg.get('id') != self.last_message_id:
                    new_messages.append(msg)
                else:
                    break
            messages = new_messages
            logger.info(f"过滤后剩余 {len(messages)} 条新消息")

        saved_files = self.save_messages(messages)

        logger.info("=" * 60)
        logger.info(f"获取完成，共 {len(messages)} 条消息，保存到 {len(saved_files)} 个文件")
        logger.info("=" * 60)

        return saved_files


def run_once():
    """运行一次"""
    config = load_config()
    getter = WindMessageGetter(config)
    saved = getter.run()
    return saved


def run_auto(config: Dict = None):
    """自动运行模式"""
    config = config or load_config()
    getter = WindMessageGetter(config)
    interval = config.get('run_interval', 300)

    logger.info(f"启动自动获取模式，间隔 {interval} 秒")
    logger.info("按 Ctrl+C 停止")

    def signal_handler(sig, frame):
        logger.info("\n收到停止信号，正在退出...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    while True:
        try:
            logger.info(f"\n[{datetime.now()}] 开始获取消息...")
            saved = getter.run()

            logger.info(f"[{datetime.now()}] 完成，等待 {interval} 秒...")
            time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("用户中断，停止自动运行")
            break
        except Exception as e:
            logger.error(f"运行出错: {e}")
            time.sleep(60)


def show_config():
    """显示配置"""
    config = load_config()
    print("\n" + "=" * 60)
    print("Wind服务号消息获取配置")
    print("=" * 60)
    print(f"服务号名称: {config.get('service_name')}")
    print(f"输出格式: {config.get('output_format')}")
    print(f"输出目录: {config.get('output_dir')}")
    print(f"最大消息数: {config.get('max_messages')}")
    print(f"自动运行: {'是' if config.get('auto_run') else '否'}")
    print(f"运行间隔: {config.get('run_interval')} 秒")
    print("=" * 60)


def debug_windows():
    """调试：列出所有窗口，帮助找出微信窗口名称"""
    try:
        import uiautomation as auto
        print("\n" + "=" * 60)
        print("调试：列出所有顶层窗口")
        print("=" * 60)
        
        windows = auto.GetRootControl().GetChildren()
        for i, win in enumerate(windows[:30], 1):
            name = win.Name or "(无名称)"
            classname = win.ClassName or "(无类名)"
            if "微信" in name or "WeChat" in name or "Weixin" in name or "微信" in classname:
                print(f"[微信相关] {i}. Name: {name[:50]}, Class: {classname}")
            elif name != "(无名称)" and len(name) > 1:
                print(f"{i}. Name: {name[:50]}, Class: {classname}")
        print("=" * 60)
    except Exception as e:
        print(f"调试失败: {e}")


def debug_wechat_structure():
    """调试：查看微信窗口的内部结构"""
    try:
        import uiautomation as auto
        
        print("\n" + "=" * 60)
        print("调试：微信窗口内部结构")
        print("=" * 60)
        
        # 找到微信窗口
        wechat = auto.WindowControl(Name="微信")
        if not wechat.Exists(2):
            print("找不到微信窗口")
            return
        
        print(f"微信窗口: {wechat.Name}, Class: {wechat.ClassName}")
        print("\n--- 微信窗口的子控件 (前50个) ---")
        
        # 获取所有子控件
        def print_control(ctrl, depth=0, max_depth=4):
            if depth > max_depth:
                return
            indent = "  " * depth
            name = ctrl.Name[:40] if ctrl.Name else "(无名称)"
            classname = ctrl.ClassName or "(无类名)"
            ctrl_type = ctrl.ControlTypeName or ""
            print(f"{indent}[{ctrl_type}] Name: {name}, Class: {classname}")
            
            children = ctrl.GetChildren()
            for i, child in enumerate(children[:15]):  # 每层最多显示15个
                print_control(child, depth + 1, max_depth)
        
        print_control(wechat)
        print("=" * 60)
        
    except Exception as e:
        print(f"调试失败: {e}")


def update_config():
    """更新配置"""
    config = load_config()

    print("\n" + "=" * 60)
    print("更新配置（直接回车保持原值）")
    print("=" * 60)

    name = input(f"服务号名称 [{config.get('service_name')}]: ").strip()
    if name:
        config['service_name'] = name

    print("\n输出格式: 1=json, 2=txt, 3=csv")
    fmt = input("请选择 [1]: ").strip()
    if fmt == '2':
        config['output_format'] = 'txt'
    elif fmt == '3':
        config['output_format'] = 'csv'
    else:
        config['output_format'] = 'json'

    max_msg = input(f"最大消息数 [{config.get('max_messages')}]: ").strip()
    if max_msg.isdigit():
        config['max_messages'] = int(max_msg)

    auto = input(f"自动运行 (y/n) [n]: ").strip().lower()
    if auto == 'y':
        config['auto_run'] = True
        interval = input(f"运行间隔(秒) [{config.get('run_interval')}]: ").strip()
        if interval.isdigit():
            config['run_interval'] = int(interval)
    else:
        config['auto_run'] = False

    save_config(config)
    print("\n配置已保存!")


def main():
    """主函数"""
    # 确保uiautomation已安装
    if not ensure_uiautomation():
        print("\n无法安装uiautomation库，请检查您的Python环境")
        return

    print("\n" + "=" * 60)
    print("Wind服务号消息获取工具")
    print("=" * 60)
    print("功能：通过微信PC版获取Wind服务号推送的消息")
    print("=" * 60)

    show_config()

    while True:
        print("\n操作选项:")
        print("1. 获取一次消息")
        print("2. 自动定时获取")
        print("3. 更新配置")
        print("4. 查看配置")
        print("5. 调试：列出窗口")
        print("6. 调试：微信结构")
        print("7. 退出")

        choice = input("\n请选择 (1-7): ").strip()

        if choice == '1':
            run_once()

        elif choice == '2':
            print("\n启动自动获取模式...")
            print("提示：请确保微信PC版已登录")
            print("按 Ctrl+C 停止\n")
            run_auto()

        elif choice == '3':
            update_config()
            show_config()

        elif choice == '4':
            show_config()

        elif choice == '5':
            debug_windows()

        elif choice == '6':
            debug_wechat_structure()

        elif choice == '7':
            print("\n再见!")
            break

        else:
            print("无效选项")


if __name__ == "__main__":
    main()
