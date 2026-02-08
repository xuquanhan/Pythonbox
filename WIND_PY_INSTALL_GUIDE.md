# WindPy模块安装配置指南

## 一、前置条件

1. **安装Wind金融终端**
   - 从Wind官网（https://www.wind.com.cn/）下载最新版本的Wind金融终端
   - 按照安装向导完成安装
   - 启动Wind金融终端并使用您的账号登录

2. **确认Python环境**
   - 确保您的Python版本与Wind金融终端兼容（建议使用Python 3.7-3.9）
   - 您当前的Python版本：3.13.3（可能需要确认兼容性）

## 二、WindPy模块安装方法

### 方法一：通过Wind金融终端自动安装

1. **打开Wind金融终端**
2. **进入Python接口配置**
   - 在Wind金融终端主界面，点击顶部菜单栏的【量化】
   - 选择【Python接口】
   - 选择【安装/升级Python接口】
3. **选择Python环境**
   - 在弹出的窗口中，选择您要配置的Python环境
   - 确保选择的是您当前使用的虚拟环境（C:\Dev\PythonBox\.venv）
4. **点击安装**
   - 等待安装完成，系统会自动将WindPy模块安装到您选择的Python环境中

### 方法二：手动复制WindPy模块

如果自动安装失败，您可以尝试手动安装：

1. **找到WindPy模块文件**
   - Wind金融终端默认安装路径：C:\Wind\Wind.NET.Client\X64
   - 在该目录下找到 `WindPy.py` 文件
   - 同时找到 `WindPy.pyd` 文件（可能在子目录中）

2. **复制到Python环境**
   - 将找到的WindPy相关文件复制到您的Python虚拟环境的site-packages目录：
     ```
     C:\Dev\PythonBox\.venv\Lib\site-packages
     ```

## 三、验证安装

安装完成后，运行以下命令验证WindPy是否正确安装：

```python
# 运行测试脚本
python test_windpy.py
```

如果看到以下输出，说明安装成功：
```
测试WindPy导入...
WindPy导入成功！
尝试启动Wind API...
Wind API启动成功！
测试获取数据...
数据获取成功，返回代码: 0
数据长度: X
日期范围: XXXX-XX-XX 到 XXXX-XX-XX
价格数据: [X.XX, X.XX, X.XX, X.XX, X.XX]...
测试完成！
```

## 四、常见问题及解决方案

### 1. WindPy导入失败
- **问题**：`No module named 'WindPy'`
- **解决方案**：确认WindPy模块已正确安装到当前Python环境的site-packages目录

### 2. Wind API连接失败
- **问题**：`Wind API连接失败，请确保Wind金融终端已启动并登录`
- **解决方案**：
  - 确保Wind金融终端已启动
  - 确保您已使用有效账号登录Wind金融终端
  - 检查网络连接是否正常

### 3. 数据获取失败
- **问题**：`Wind API错误: XXXX，请检查股票代码是否正确`
- **解决方案**：
  - 确认股票代码格式正确（如：000001.SZ表示深圳证券交易所的平安银行）
  - 确认您的Wind账号有获取该数据的权限
  - 检查Wind金融终端是否正常运行

## 五、股票代码格式说明

在Wind系统中，股票代码需要包含交易所后缀：

- **上海证券交易所**：.SH（如：600000.SH 浦发银行）
- **深圳证券交易所**：.SZ（如：000001.SZ 平安银行）
- **创业板**：.SZ（如：300001.SZ 特锐德）
- **科创板**：.SH（如：688001.SH 华兴源创）

## 六、联系支持

如果您在安装和配置过程中遇到问题，可以：

1. **联系Wind客服**：400-888-9559
2. **访问Wind社区**：https://bbs.wind.com.cn/
3. **查看Wind帮助文档**：在Wind金融终端中按F1查看帮助

---

安装配置完成后，您就可以使用股票滚动收益率分位数分析器进行实时数据分析了！
