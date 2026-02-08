# 测试WindPy是否可以正常导入和使用
print("测试WindPy导入...")
try:
    from WindPy import w
    print("WindPy导入成功！")
    
    # 尝试启动Wind API
    print("尝试启动Wind API...")
    w.start()
    print("Wind API启动成功！")
    
    # 测试获取数据
    print("测试获取数据...")
    data = w.wsd("000001.SZ", "close", "2024-01-01", "2024-01-10")
    print(f"数据获取成功，返回代码: {data.ErrorCode}")
    if data.ErrorCode == 0:
        print(f"数据长度: {len(data.Data[0])}")
        print(f"日期范围: {data.Times[0]} 到 {data.Times[-1]}")
        print(f"价格数据: {data.Data[0][:5]}...")
    
    w.stop()
    print("测试完成！")
except ImportError as e:
    print(f"WindPy导入失败: {str(e)}")
except Exception as e:
    print(f"其他错误: {str(e)}")
