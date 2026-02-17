#!/usr/bin/env python3
"""
微信数据库解密工具
用于获取微信数据库的解密密钥并解密数据库
"""

import os
import sys
import ctypes
import ctypes.wintypes
import subprocess
import re
import hashlib
import hmac
import struct
import sqlite3
from typing import Optional, Tuple, List

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("警告: pycryptodome 未安装，请运行: pip install pycryptodome")

def find_wechat_process() -> Optional[int]:
    """查找微信进程"""
    try:
        result = subprocess.run(
            ['tasklist', '/fi', 'imagename eq Weixin.exe', '/fo', 'csv', '/nh'],
            capture_output=True, text=True, encoding='gbk'
        )
        
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if 'Weixin.exe' in line:
                parts = line.split(',')
                if len(parts) >= 2:
                    pid = int(parts[1].strip('"'))
                    return pid
        return None
    except Exception as e:
        print(f"查找微信进程失败: {e}")
        return None

def get_wechat_key_from_memory(pid: int) -> Optional[bytes]:
    """从微信进程内存中获取数据库密钥"""
    try:
        kernel32 = ctypes.windll.kernel32
        
        PROCESS_VM_READ = 0x0010
        PROCESS_QUERY_INFORMATION = 0x0400
        
        handle = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
        if not handle:
            print(f"无法打开进程 {pid}")
            return None
        
        try:
            # 读取进程内存
            # 这里简化实现，实际需要更复杂的内存搜索
            # 微信密钥通常是 32 字节的 AES 密钥
            
            # 使用 pymem 或其他工具会更可靠
            print("正在搜索内存中的密钥...")
            print("提示: 完整实现需要安装 pymem 库")
            
            return None
        finally:
            kernel32.CloseHandle(handle)
            
    except Exception as e:
        print(f"读取内存失败: {e}")
        return None

def try_decrypt_with_key(db_path: str, key: bytes) -> bool:
    """尝试使用密钥解密数据库"""
    if not CRYPTO_AVAILABLE:
        print("pycryptodome 未安装，无法解密")
        return False
    
    try:
        with open(db_path, 'rb') as f:
            header = f.read(4096)
        
        # SQLCipher 使用 AES-256-CBC
        # 尝试解密第一页
        # 这需要知道确切的加密参数
        
        return False
    except Exception as e:
        print(f"解密失败: {e}")
        return False

def check_wechat_running() -> bool:
    """检查微信是否正在运行"""
    pid = find_wechat_process()
    if pid:
        print(f"微信正在运行，PID: {pid}")
        return True
    else:
        print("微信未运行")
        return False

def get_key_from_config() -> Optional[bytes]:
    """从配置文件中获取密钥（如果之前保存过）"""
    key_file = "F:/xwechat_files/xuquanhan_450f/config/key_info.dat"
    if os.path.exists(key_file):
        try:
            with open(key_file, 'rb') as f:
                return f.read()
        except:
            pass
    return None

def main():
    print("=" * 60)
    print("微信数据库解密工具")
    print("=" * 60)
    
    db_path = "F:/xwechat_files/xuquanhan_450f/db_storage/message/message_0.db"
    
    # 检查微信是否运行
    print("\n[1] 检查微信运行状态...")
    wechat_running = check_wechat_running()
    
    if wechat_running:
        pid = find_wechat_process()
        print(f"\n[2] 尝试从内存获取密钥...")
        print("    注意: 这需要管理员权限")
        
        # 尝试获取密钥
        key = get_wechat_key_from_memory(pid)
        
        if key:
            print(f"    成功获取密钥: {key.hex()}")
            
            # 尝试解密
            print("\n[3] 尝试解密数据库...")
            if try_decrypt_with_key(db_path, key):
                print("    解密成功!")
            else:
                print("    解密失败")
        else:
            print("    无法从内存获取密钥")
            print("\n    替代方案:")
            print("    1. 使用 PyWxDump 工具")
            print("    2. 使用 wxauto 库")
            print("    3. 手动导出聊天记录")
    else:
        print("\n[!] 微信未运行，请先启动微信并登录")
        print("    然后重新运行此脚本")
    
    print("\n" + "=" * 60)
    print("\n推荐使用 PyWxDump 工具:")
    print("  pip install pywxdump")
    print("  wxdump bias addr")
    print("=" * 60)

if __name__ == "__main__":
    main()
