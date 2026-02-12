# 将三个skill转换为全局skill的计划

## 问题分析
用户希望将项目中的三个skill（code-efficiency-checker、git-sync-reminder、project-structure-organizer）改为全局skill，以便在所有项目中使用。

## 解决方案

### 步骤1：检查全局skill目录
- 检查Trae的安装目录和用户目录，寻找全局skill的存储位置
- 通常全局skill可能存储在用户的AppData目录下的Trae相关文件夹中

### 步骤2：创建全局skill目录（如果不存在）
- 如果未找到全局skill目录，将在适当的位置创建
- 可能的位置：`C:\Users\xuqua\AppData\Roaming\Trae\skills`

### 步骤3：复制skill文件到全局目录
- 将项目中的三个skill文件夹复制到全局skill目录
- 确保所有文件结构保持完整

### 步骤4：验证全局skill是否生效
- 重启Trae IDE
- 检查是否可以在其他项目中访问这些skill

### 步骤5：清理项目特定的skill（可选）
- 如果用户希望完全移除项目特定的skill，可以删除项目中的`.trae/skills/`目录

## 预期结果
三个skill将成为全局skill，可在所有项目中使用，而不仅仅局限于PythonBox项目。