#!/usr/bin/env python
# -*- coding: utf-8 -*-

def convert_gbk_to_utf8():
    # 原始文件路径
    original_file = r'C:\Onedrive\Work\ICBC\报告\常规报告\量化月报\月度量化预测模型\模型\预测黄金\predict_classification_gold.py'
    
    # 读取原始二进制内容
    with open(original_file, 'rb') as f:
        raw_bytes = f.read()
    
    # 尝试使用GBK解码（因为中文Windows系统通常使用GBK编码）
    try:
        # 将原始字节按照GBK编码解码，然后以UTF-8编码保存
        gbk_decoded = raw_bytes.decode('gbk')
        
        # 输出修复后的文件
        output_file = r'C:\Dev\PythonBox\predict_classification_gold_fixed_gbk.py'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(gbk_decoded)
        
        print("成功使用GBK解码并转换为UTF-8编码")
        print(f"修复后的文件已保存到: {output_file}")
        
        # 验证修复结果
        with open(output_file, 'r', encoding='utf-8') as f:
            sample = f.read(500)  # 读取前500个字符作为样本
            print("修复后文件的前500个字符预览:")
            print(sample[:200])
        
    except UnicodeDecodeError as e:
        print(f"GBK解码失败: {e}")
        
        # 尝试使用错误容错模式
        try:
            gbk_decoded = raw_bytes.decode('gbk', errors='replace')
            
            # 输出修复后的文件
            output_file = r'C:\Dev\PythonBox\predict_classification_gold_fixed_gbk.py'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(gbk_decoded)
            
            print("使用错误容错模式成功转换")
            print(f"修复后的文件已保存到: {output_file}")
            
        except Exception as e2:
            print(f"转换失败: {e2}")

if __name__ == "__main__":
    convert_gbk_to_utf8()