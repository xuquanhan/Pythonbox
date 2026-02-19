#!/usr/bin/env python3
"""
Wind服务号消息获取脚本（数据库方式）
直接从微信PC版数据库读取Wind服务号推送的消息
"""

import os
import sys
import json
import time
import sqlite3
import logging
import subprocess
from datetime import datetime
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/wind_message_db.log', encoding='utf-8'),
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
        'wechat_data_dir': '',
        'last_message_id': ''
    }


def save_config(config: Dict):
    """保存配置文件"""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")


def find_wechat_data_dirs() -> List[Dict]:
    """查找微信数据目录"""
    possible_paths = []
    
    # 常见路径
    base_paths = [
        os.path.expanduser("~/Documents/WeChat Files"),
        "C:/Users/Public/Documents/WeChat Files",
    ]
    
    # 添加所有用户目录
    users_dir = "C:/Users"
    if os.path.exists(users_dir):
        for user in os.listdir(users_dir):
            user_path = os.path.join(users_dir, user)
            if os.path.isdir(user_path):
                base_paths.append(os.path.join(user_path, "Documents", "WeChat Files"))
    
    for base in base_paths:
        if not os.path.exists(base):
            continue
        
        for folder in os.listdir(base):
            folder_path = os.path.join(base, folder)
            if not os.path.isdir(folder_path):
                continue
            
            # 检查是否是微信用户目录
            if folder.startswith("wxid_") or "WeChat" not in folder:
                msg_path = os.path.join(folder_path, "Msg")
                if os.path.exists(msg_path):
                    possible_paths.append({
                        'wxid': folder,
                        'path': folder_path,
                        'msg_path': msg_path
                    })
    
    return possible_paths


def check_pywxdump() -> bool:
    """检查pywxdump是否安装"""
    try:
        import pywxdump
        return True
    except ImportError:
        return False


def install_pywxdump() -> bool:
    """安装pywxdump"""
    logger.info("正在安装 pywxdump...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pywxdump'])
        return True
    except Exception as e:
        logger.error(f"安装失败: {e}")
        return False


def get_wechat_key() -> Optional[bytes]:
    """获取微信数据库密钥"""
    try:
        from pywxdump import get_wx_info
        
        wx_info = get_wx_info()
        if wx_info:
            for info in wx_info:
                key = info.get('key')
                if key:
                    logger.info(f"获取到密钥，微信ID: {info.get('wxid')}")
                    return key
        return None
    except Exception as e:
        logger.error(f"获取密钥失败: {e}")
        return None


def decrypt_db(db_path: str, key: bytes, output_path: str) -> bool:
    """解密数据库"""
    try:
        from pywxdump import decrypt_merge
        result = decrypt_merge(db_path, output_path, key)
        return bool(result)
    except Exception as e:
        logger.error(f"解密失败: {e}")
        return False


class WindMessageDBReader:
    """Wind服务号消息数据库读取器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or load_config()
        self.service_name = self.config.get('service_name', 'Wind金融终端')
        self.output_format = self.config.get('output_format', 'json')
        self.output_dir = self.config.get('output_dir', OUTPUT_DIR)
        self.max_messages = self.config.get('max_messages', 50)
        self.last_message_id = self.config.get('last_message_id', '')
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.key = None
        self.db_path = None
        self.decrypted_db_path = None
    
    def find_message_db(self) -> Optional[str]:
        """查找消息数据库"""
        data_dirs = find_wechat_data_dirs()
        
        for data in data_dirs:
            msg_path = data['msg_path']
            
            # 查找 MSG*.db 文件
            for f in os.listdir(msg_path):
                if f.startswith('MSG') and f.endswith('.db'):
                    db_file = os.path.join(msg_path, f)
                    logger.info(f"找到数据库: {db_file}")
                    return db_file
            
            # 也检查 Multi 目录
            multi_path = os.path.join(msg_path, 'Multi')
            if os.path.exists(multi_path):
                for f in os.listdir(multi_path):
                    if f.startswith('MSG') and f.endswith('.db'):
                        db_file = os.path.join(multi_path, f)
                        logger.info(f"找到数据库: {db_file}")
                        return db_file
        
        return None
    
    def init_key(self) -> bool:
        """初始化密钥"""
        if self.key:
            return True
        
        logger.info("正在获取微信数据库密钥...")
        self.key = get_wechat_key()
        
        if self.key:
            logger.info("密钥获取成功")
            return True
        else:
            logger.error("密钥获取失败，请确保微信正在运行")
            return False
    
    def read_messages_from_db(self, db_path: str) -> List[Dict]:
        """从数据库读取消息"""
        messages = []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 查找消息表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"数据库表: {tables[:10]}...")
            
            # 尝试查找包含消息的表
            msg_table = None
            for table in ['MSG', 'message', 'messages', 'ChatMsg']:
                if table in tables:
                    msg_table = table
                    break
            
            if not msg_table:
                # 尝试 MSG0, MSG1 等表
                for table in tables:
                    if table.startswith('MSG'):
                        msg_table = table
                        break
            
            if not msg_table:
                logger.warning("找不到消息表")
                conn.close()
                return messages
            
            logger.info(f"使用消息表: {msg_table}")
            
            # 查询消息
            # 微信消息表结构可能不同，尝试几种常见结构
            try:
                # 尝试获取表结构
                cursor.execute(f"PRAGMA table_info({msg_table})")
                columns = [row[1] for row in cursor.fetchall()]
                logger.info(f"表字段: {columns[:15]}...")
                
                # 构建查询
                if 'content' in columns and 'createTime' in columns:
                    query = f"""
                        SELECT content, createTime, talker, type 
                        FROM {msg_table} 
                        WHERE content LIKE ? 
                        ORDER BY createTime DESC 
                        LIMIT ?
                    """
                    cursor.execute(query, (f'%{self.service_name}%', self.max_messages))
                elif 'StrContent' in columns:
                    query = f"""
                        SELECT StrContent, CreateTime, StrTalker, Type 
                        FROM {msg_table} 
                        WHERE StrContent LIKE ? 
                        ORDER BY CreateTime DESC 
                        LIMIT ?
                    """
                    cursor.execute(query, (f'%{self.service_name}%', self.max_messages))
                else:
                    # 通用查询
                    cursor.execute(f"SELECT * FROM {msg_table} LIMIT 5")
                    sample = cursor.fetchall()
                    logger.info(f"样本数据: {sample[:2]}")
                    conn.close()
                    return messages
                
                rows = cursor.fetchall()
                logger.info(f"查询到 {len(rows)} 条消息")
                
                for row in rows:
                    content = row[0] if row[0] else ""
                    create_time = row[1] if len(row) > 1 else 0
                    
                    if content:
                        msg_id = f"{content[:30]}_{create_time}"
                        message = {
                            'id': msg_id,
                            'type': 'text',
                            'content': content,
                            'sender': self.service_name,
                            'service_name': self.service_name,
                            'create_time': create_time,
                            'crawl_time': datetime.now().isoformat()
                        }
                        messages.append(message)
                        
            except sqlite3.Error as e:
                logger.warning(f"查询失败: {e}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"读取数据库失败: {e}")
        
        return messages
    
    def run(self) -> List[Dict]:
        """运行获取任务"""
        logger.info("=" * 60)
        logger.info("开始获取Wind服务号消息（数据库方式）")
        logger.info("=" * 60)
        
        # 1. 查找数据库
        self.db_path = self.find_message_db()
        if not self.db_path:
            logger.error("找不到微信消息数据库")
            return []
        
        # 2. 获取密钥
        if not self.init_key():
            logger.error("无法获取密钥")
            return []
        
        # 3. 解密数据库
        self.decrypted_db_path = os.path.join(self.output_dir, 'decrypted_msg.db')
        logger.info(f"正在解密数据库...")
        
        if not decrypt_db(self.db_path, self.key, self.decrypted_db_path):
            logger.error("解密失败")
            return []
        
        logger.info("解密成功")
        
        # 4. 读取消息
        messages = self.read_messages_from_db(self.decrypted_db_path)
        
        logger.info(f"获取到 {len(messages)} 条消息")
        return messages
    
    def save_messages(self, messages: List[Dict]) -> str:
        """保存消息"""
        if not messages:
            return ""
        
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
        else:
            filepath = os.path.join(self.output_dir, f'wind_messages_{timestamp}.txt')
            with open(filepath, 'w', encoding='utf-8') as f:
                for msg in messages:
                    f.write(f"{msg.get('content')}\n{'-'*40}\n")
        
        logger.info(f"消息已保存: {filepath}")
        return filepath


def run_once():
    """运行一次"""
    config = load_config()
    reader = WindMessageDBReader(config)
    messages = reader.run()
    if messages:
        reader.save_messages(messages)
    return messages


def run_auto():
    """自动运行"""
    config = load_config()
    interval = config.get('run_interval', 300)
    
    logger.info(f"启动自动获取模式，间隔 {interval} 秒")
    
    while True:
        try:
            run_once()
            logger.info(f"等待 {interval} 秒...")
            time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("用户中断")
            break
        except Exception as e:
            logger.error(f"运行出错: {e}")
            time.sleep(60)


def show_config():
    """显示配置"""
    config = load_config()
    print("\n" + "=" * 60)
    print("Wind服务号消息获取配置（数据库方式）")
    print("=" * 60)
    print(f"服务号名称: {config.get('service_name')}")
    print(f"输出格式: {config.get('output_format')}")
    print(f"输出目录: {config.get('output_dir')}")
    print(f"最大消息数: {config.get('max_messages')}")
    print(f"运行间隔: {config.get('run_interval')} 秒")
    print("=" * 60)


def main():
    """主函数"""
    # 检查pywxdump
    if not check_pywxdump():
        print("pywxdump 未安装，正在安装...")
        if not install_pywxdump():
            print("安装失败，请手动运行: pip install pywxdump")
            return
    
    print("\n" + "=" * 60)
    print("Wind服务号消息获取工具（数据库方式）")
    print("=" * 60)
    print("功能：直接从微信PC版数据库读取Wind服务号消息")
    print("注意：需要微信正在运行以获取密钥")
    print("=" * 60)
    
    show_config()
    
    while True:
        print("\n操作选项:")
        print("1. 获取一次消息")
        print("2. 自动定时获取")
        print("3. 查看配置")
        print("4. 退出")
        
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == '1':
            run_once()
        elif choice == '2':
            run_auto()
        elif choice == '3':
            show_config()
        elif choice == '4':
            print("\n再见!")
            break
        else:
            print("无效选项")


if __name__ == "__main__":
    main()
