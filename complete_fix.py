#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

def fix_encoding():
    # 原始文件路径
    original_file = r'C:\Onedrive\Work\ICBC\报告\常规报告\量化月报\月度量化预测模型\模型\预测黄金\predict_classification_gold.py'
    # 输出修复后文件路径
    output_file = r'C:\Dev\PythonBox\predict_classification_gold_completely_fixed.py'
    
    # 以二进制模式读取原始文件
    with open(original_file, 'rb') as f:
        content_bytes = f.read()
    
    # 尝试用GBK解码（这是最可能的原始编码）
    try:
        content = content_bytes.decode('gbk')
        print("使用GBK成功解码原始文件")
    except UnicodeDecodeError:
        # 如果GBK失败，尝试gb2312
        try:
            content = content_bytes.decode('gb2312')
            print("使用GB2312成功解码原始文件")
        except UnicodeDecodeError:
            # 如果都失败，使用错误忽略模式
            content = content_bytes.decode('gbk', errors='ignore')
            print("使用错误忽略模式解码原始文件")
    
    # 保存修复后的文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"修复完成，文件已保存到: {output_file}")

if __name__ == "__main__":
    fix_encoding()