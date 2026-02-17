#!/usr/bin/env python3
"""
使用 PyWxDump 获取微信数据库密钥
"""

import os
import sys

def get_wechat_key():
    """获取微信数据库密钥"""
    try:
        from pywxdump import get_wx_info, decrypt_merge
        
        print("=" * 60)
        print("微信数据库密钥获取工具")
        print("=" * 60)
        
        # 获取微信信息
        print("\n[1] 获取微信信息...")
        wx_info = get_wx_info()
        
        if not wx_info:
            print("未找到微信信息，请确保微信已登录")
            return None
        
        for i, info in enumerate(wx_info):
            print(f"\n微信账号 {i+1}:")
            print(f"  微信ID: {info.get('wxid', 'N/A')}")
            print(f"  昵称: {info.get('nickname', 'N/A')}")
            print(f"  手机: {info.get('mobile', 'N/A')}")
            print(f"  微信路径: {info.get('wxdir', 'N/A')}")
            print(f"  密钥: {info.get('key', 'N/A')}")
            
            if info.get('key'):
                return info['key']
        
        return None
        
    except ImportError as e:
        print(f"导入 pywxdump 失败: {e}")
        return None
    except Exception as e:
        print(f"获取密钥失败: {e}")
        return None

def decrypt_database(db_path: str, key: bytes, output_path: str):
    """解密数据库"""
    try:
        from pywxdump import decrypt_merge
        
        print(f"\n[2] 解密数据库...")
        print(f"    输入: {db_path}")
        print(f"    输出: {output_path}")
        
        result = decrypt_merge(db_path, output_path, key)
        
        if result:
            print("    解密成功!")
            return True
        else:
            print("    解密失败")
            return False
            
    except Exception as e:
        print(f"解密失败: {e}")
        return False

def main():
    # 获取密钥
    key = get_wechat_key()
    
    if key:
        print(f"\n成功获取密钥: {key.hex() if isinstance(key, bytes) else key}")
        
        # 解密数据库
        db_path = "F:/xwechat_files/xuquanhan_450f/db_storage/message/message_0.db"
        output_path = "F:/xwechat_files/xuquanhan_450f/db_storage/message/message_0_decrypted.db"
        
        if os.path.exists(db_path):
            decrypt_database(db_path, key, output_path)
    else:
        print("\n无法获取密钥")
        print("\n请确保:")
        print("1. 微信已登录")
        print("2. 以管理员权限运行此脚本")

if __name__ == "__main__":
    main()
