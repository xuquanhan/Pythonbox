## 计划概述
创建一个名为 `code-efficiency-checker` 的SKILL，用于在每次创建或修改代码后自动检查代码效率。

## SKILL结构

### 1. 目录结构
```
.trae/skills/code-efficiency-checker/
└── SKILL.md
```

### 2. SKILL.md 内容

**Frontmatter:**
- name: "code-efficiency-checker"
- description: "检查Python代码的性能瓶颈和效率问题。Invoke when user creates/modifies code or asks for performance optimization."

**正文内容将包括：**

1. **性能检查清单**
   - 时间复杂度分析
   - 空间复杂度分析
   - 循环优化检查
   - 数据结构选择检查
   - I/O操作优化检查

2. **常见性能陷阱**
   - 在循环中使用列表的append vs 预分配
   - 不必要的类型转换
   - 重复计算
   - 过度使用全局变量
   - 低效的字符串拼接

3. **性能分析工具使用**
   - cProfile 使用方法
   - timeit 使用方法
   - memory_profiler 使用方法
   - line_profiler 使用方法

4. **优化建议模板**
   - 提供具体的代码优化示例
   - 对比优化前后的性能差异
   - 解释为什么这样优化更好

5. **检查流程**
   - 步骤1: 静态代码分析
   - 步骤2: 运行性能测试
   - 步骤3: 生成优化报告
   - 步骤4: 提供具体建议

## 预期效果
- 自动识别代码中的性能问题
- 提供具体的优化建议
- 帮助用户写出更高效的代码
- 养成性能意识

请确认此计划后，我将创建该SKILL。