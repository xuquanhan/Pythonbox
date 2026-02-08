#!/usr/bin/env python
# -*- coding: utf-8 -*-

def decode_chinese_characters():
    # 读取原始文件的二进制内容
    original_file = r'C:\Onedrive\Work\ICBC\报告\常规报告\量化月报\月度量化预测模型\模型\预测黄金\predict_classification_gold.py'
    
    with open(original_file, 'rb') as f:
        raw_bytes = f.read()
    
    # 首先尝试用cp936解码（这是GBK的超集，常用于Windows系统）
    try:
        decoded_content = raw_bytes.decode('cp936')
        
        # 保存修复后的文件
        output_file = r'C:\Dev\PythonBox\predict_classification_gold_decoded.py'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(decoded_content)
        
        print("成功使用cp936解码并保存为UTF-8格式")
        print(f"文件已保存到: {output_file}")
        
        # 验证结果
        with open(output_file, 'r', encoding='utf-8') as f:
            sample = f.read(1000)
            print("修复后文件内容预览:")
            print(sample[:300])
            
    except UnicodeDecodeError:
        print("cp936解码失败，尝试其他方法")
        
        # 尝试使用latin-1解码然后重新编码
        try:
            # 先用latin-1解码（这会保留原始字节值）
            temp_str = raw_bytes.decode('latin-1')
            
            # 将字符串转换为字节，再用cp936解码
            temp_bytes = temp_str.encode('latin-1')
            
            # 尝试用cp936解码
            decoded_content = temp_bytes.decode('cp936', errors='replace')
            
            # 保存修复后的文件
            output_file = r'C:\Dev\PythonBox\predict_classification_gold_decoded.py'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(decoded_content)
            
            print("使用latin-1中间转换成功解码并保存为UTF-8格式")
            print(f"文件已保存到: {output_file}")
            
        except Exception as e:
            print(f"解码失败: {e}")
            print("尝试最后的修复方法")
            
            # 最后尝试：直接用错误替换的方式解码
            try:
                decoded_content = raw_bytes.decode('utf-8', errors='replace')
                
                # 保存修复后的文件
                output_file = r'C:\Dev\PythonBox\predict_classification_gold_decoded.py'
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(decoded_content)
                
                print("使用UTF-8错误替换模式解码成功")
                print(f"文件已保存到: {output_file}")
                
            except Exception as e2:
                print(f"所有解码方法都失败了: {e2}")

if __name__ == "__main__":
    decode_chinese_characters()