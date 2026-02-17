#!/usr/bin/env python3
"""
微信数据库检查工具
用于检查微信数据库是否加密，以及数据库结构
"""

import sqlite3
import os
import struct

def check_db_encryption(db_path):
    """检查数据库是否加密"""
    try:
        with open(db_path, 'rb') as f:
            header = f.read(16)
        
        if header[:16] == b'SQLite format 3\x00':
            return False, "未加密 (SQLite 格式)"
        elif header[:15] == b'SQLite format 3':
            return False, "未加密 (SQLite 格式)"
        else:
            return True, f"已加密 (头部: {header[:8].hex()})"
    except Exception as e:
        return None, f"检查失败: {e}"

def read_db_tables(db_path):
    """读取数据库表结构"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        conn.close()
        return [t[0] for t in tables], None
    except Exception as e:
        return None, str(e)

def main():
    db_path = "F:/xwechat_files/xuquanhan_450f/db_storage/message/message_0.db"
    
    print("=" * 60)
    print("微信数据库检查工具")
    print("=" * 60)
    print(f"\n数据库路径: {db_path}")
    print(f"文件大小: {os.path.getsize(db_path) / 1024 / 1024:.2f} MB")
    
    # 检查加密状态
    print("\n[1] 检查数据库加密状态...")
    is_encrypted, status = check_db_encryption(db_path)
    print(f"    状态: {status}")
    
    if is_encrypted:
        print("\n[!] 数据库已加密，需要解密才能读取内容")
        print("    解密方法:")
        print("    1. 从微信进程内存中获取密钥")
        print("    2. 使用第三方工具解密")
    else:
        print("\n[2] 尝试读取数据库表结构...")
        tables, error = read_db_tables(db_path)
        
        if tables:
            print(f"    找到 {len(tables)} 个表:")
            for table in tables:
                print(f"    - {table}")
        else:
            print(f"    读取失败: {error}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
