import codecs

# 尝试以二进制模式读取文件，然后用不同编码尝试解码
file_path = r'C:\Onedrive\Work\ICBC\报告\常规报告\量化月报\月度量化预测模型\模型\预测黄金\predict_classification_gold.py'

with open(file_path, 'rb') as f:
    raw_content = f.read()

# 尝试不同编码解码
encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'iso-8859-1', 'cp1252']

for encoding in encodings:
    try:
        content = raw_content.decode(encoding)
        print(f"成功使用 {encoding} 编码解码文件")
        
        # 检查解码后的内容是否包含中文
        if '预测' in content or '数据' in content or '模型' in content:
            print(f"确认 {encoding} 是正确的编码")
            
            # 以UTF-8编码保存修复后的文件
            output_path = r'C:\Dev\PythonBox\predict_classification_gold_fixed.py'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"已将修复后的文件保存到: {output_path}")
            break
        else:
            print(f"{encoding} 解码后没有找到预期的中文内容")
    except UnicodeDecodeError:
        print(f"使用 {encoding} 编码解码失败")
        continue
else:
    print("所有编码尝试都失败了")
    # 作为最后手段，尝试忽略错误
    try:
        content = raw_content.decode('gbk', errors='ignore')
        output_path = r'C:\Dev\PythonBox\predict_classification_gold_fixed.py'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"使用错误忽略模式解码并保存到: {output_path}")
    except:
        print("错误忽略模式也失败了")