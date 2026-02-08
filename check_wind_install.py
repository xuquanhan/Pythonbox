import os
import glob

def check_wind_installation():
    """检查Wind金融终端是否安装"""
    # 检查常见安装路径
    common_paths = [
        "C:\\Wind",
        "D:\\Wind",
        "C:\\Program Files\\Wind",
        "C:\\Program Files (x86)\\Wind"
    ]
    
    print("检查常见安装路径...")
    found_wind = False
    
    for path in common_paths:
        if os.path.exists(path):
            print(f"路径存在: {path}")
            found_wind = True
            # 检查是否有WindPy.pyd文件
            windpy_files = glob.glob(os.path.join(path, "**", "WindPy.pyd"), recursive=True)
            if windpy_files:
                print(f"找到WindPy.pyd文件: {windpy_files[0]}")
            else:
                print("未找到WindPy.pyd文件")
                # 列出目录内容
                print("目录内容:")
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        print(f"  目录: {item}")
                    else:
                        print(f"  文件: {item}")
        else:
            print(f"路径不存在: {path}")
    
    if not found_wind:
        print("\n未找到Wind金融终端安装目录")
    
    # 检查site-packages中的WindPy文件
    print("\n检查Python环境中的WindPy文件...")
    site_packages = os.path.join(os.path.dirname(os.path.dirname(os.__file__)), "site-packages")
    print(f"Site-packages路径: {site_packages}")
    
    if os.path.exists(site_packages):
        windpy_files = glob.glob(os.path.join(site_packages, "*WindPy*"))
        if windpy_files:
            print("找到WindPy相关文件:")
            for f in windpy_files:
                print(f"  - {os.path.basename(f)}")
        else:
            print("未找到WindPy相关文件")
    else:
        print("Site-packages路径不存在")

if __name__ == "__main__":
    check_wind_installation()
