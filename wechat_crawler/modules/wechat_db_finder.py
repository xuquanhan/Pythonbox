#!/usr/bin/env python3
"""
微信数据库定位工具
用于查找微信PC版的数据库文件位置
"""

import os
import glob
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_wechat_db():
    """查找微信数据库文件"""
    
    # 常见的微信数据目录位置
    possible_paths = [
        os.path.expanduser("~/Documents/WeChat Files"),
        os.path.expanduser("~/WeChat Files"),
        "C:/Users/Public/Documents/WeChat Files",
        "D:/WeChat Files",
        "E:/WeChat Files",
    ]
    
    # 获取所有用户目录
    users_dir = "C:/Users"
    if os.path.exists(users_dir):
        for user in os.listdir(users_dir):
            user_path = os.path.join(users_dir, user)
            if os.path.isdir(user_path):
                possible_paths.append(os.path.join(user_path, "Documents", "WeChat Files"))
    
    found_dbs = []
    
    for base_path in possible_paths:
        if not os.path.exists(base_path):
            continue
        
        logger.info(f"检查路径: {base_path}")
        
        # 查找微信ID目录（通常以 wxid_ 开头）
        for folder in os.listdir(base_path):
            folder_path = os.path.join(base_path, folder)
            if not os.path.isdir(folder_path):
                continue
            
            # 检查是否是微信用户目录
            if folder.startswith("wxid_") or folder.startswith("WeChat"):
                # 查找 MSG 数据库文件
                msg_path = os.path.join(folder_path, "Msg", "Multi")
                if os.path.exists(msg_path):
                    db_files = glob.glob(os.path.join(msg_path, "MSG*.db"))
                    if db_files:
                        logger.info(f"找到微信用户: {folder}")
                        logger.info(f"数据库路径: {msg_path}")
                        logger.info(f"数据库文件数量: {len(db_files)}")
                        found_dbs.append({
                            "user": folder,
                            "path": msg_path,
                            "db_files": db_files
                        })
    
    return found_dbs

def check_wechat_installed():
    """检查微信是否已安装"""
    possible_install_paths = [
        "C:/Program Files/Tencent/WeChat/WeChat.exe",
        "C:/Program Files (x86)/Tencent/WeChat/WeChat.exe",
        "D:/Program Files/Tencent/WeChat/WeChat.exe",
        "D:/Program Files (x86)/Tencent/WeChat/WeChat.exe",
    ]
    
    for path in possible_install_paths:
        if os.path.exists(path):
            logger.info(f"微信已安装: {path}")
            return path
    
    logger.warning("未找到微信安装路径")
    return None

def main():
    """主函数"""
    print("=" * 60)
    print("微信数据库定位工具")
    print("=" * 60)
    
    # 检查微信是否安装
    wechat_path = check_wechat_installed()
    if wechat_path:
        print(f"\n[OK] 微信安装路径: {wechat_path}")
    else:
        print("\n[警告] 未找到微信安装路径，请确认微信已安装")
    
    # 查找数据库文件
    print("\n正在查找微信数据库文件...")
    found_dbs = find_wechat_db()
    
    if found_dbs:
        print(f"\n[成功] 找到 {len(found_dbs)} 个微信用户的数据目录:")
        for i, db_info in enumerate(found_dbs, 1):
            print(f"\n用户 {i}: {db_info['user']}")
            print(f"  数据库路径: {db_info['path']}")
            print(f"  数据库文件数量: {len(db_info['db_files'])}")
            print(f"  示例文件: {os.path.basename(db_info['db_files'][0])}")
    else:
        print("\n[未找到] 未找到微信数据库文件")
        print("\n可能的原因:")
        print("1. 微信PC版未登录过")
        print("2. 微信数据目录不在默认位置")
        print("3. 微信版本较新，数据目录结构已改变")
        print("\n建议:")
        print("1. 请先在PC上登录微信")
        print("2. 登录后重新运行此脚本")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
