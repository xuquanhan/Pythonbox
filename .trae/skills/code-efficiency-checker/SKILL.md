---
name: "code-efficiency-checker"
description: "检查Python代码的性能瓶颈和效率问题。Invoke when user creates/modifies code or asks for performance optimization."
---

# Code Efficiency Checker

This skill helps analyze Python code for performance issues and provides optimization suggestions.

## When to Invoke

- After creating or modifying Python code
- When user asks "check this code for efficiency"
- When user reports slow performance
- Before finalizing code changes
- During code review process

## Performance Checklist

### 1. Time Complexity Analysis
- [ ] Check for nested loops (O(n²) or worse)
- [ ] Identify unnecessary repeated calculations
- [ ] Look for inefficient sorting operations
- [ ] Check for linear searches in loops
- [ ] Verify algorithm choice is appropriate for data size

### 2. Space Complexity Analysis
- [ ] Check for unnecessary data duplication
- [ ] Identify memory leaks
- [ ] Look for inefficient data structures
- [ ] Check for large temporary objects
- [ ] Verify generator usage where appropriate

### 3. Common Python Performance Traps

#### List Operations
```python
# BAD: Growing list dynamically
result = []
for i in range(1000000):
    result.append(i)  # O(n) amortized, causes reallocations

# GOOD: Pre-allocate when size is known
result = [0] * 1000000
for i in range(1000000):
    result[i] = i

# BETTER: Use list comprehension
result = [i for i in range(1000000)]

# BEST: Use generator if only iterating once
result = (i for i in range(1000000))
```

#### String Concatenation
```python
# BAD: String concatenation in loop
result = ""
for s in strings:
    result += s  # O(n²) time complexity

# GOOD: Use join method
result = "".join(strings)  # O(n) time complexity
```

#### Dictionary Lookups
```python
# BAD: Checking membership before access
if key in my_dict:
    value = my_dict[key]

# GOOD: Use get method with default
value = my_dict.get(key, default_value)

# BETTER: Use try-except for expected misses
try:
    value = my_dict[key]
except KeyError:
    value = default_value
```

#### Unnecessary Type Conversions
```python
# BAD: Repeated type conversion
for i in range(len(my_list)):
    value = int(my_list[i])  # Converted every iteration

# GOOD: Convert once before loop
int_list = [int(x) for x in my_list]
for value in int_list:
    process(value)
```

### 4. Data Structure Selection

| Use Case | Recommended Structure | Avoid |
|----------|----------------------|-------|
| Fast lookup by key | dict | list |
| Ordered data with frequent insertions/deletions | deque | list |
| Unique elements with fast lookup | set | list |
| FIFO queue | deque | list |
| Priority queue | heapq | sorted list |

### 5. Pandas Optimization

```python
# BAD: Iterating over DataFrame rows
for index, row in df.iterrows():
    process(row['column'])

# GOOD: Use vectorized operations
df['new_column'] = df['column'].apply(process)

# BETTER: Use built-in vectorized functions
df['new_column'] = df['column'] * 2 + 1
```

## Performance Analysis Tools

### 1. timeit - Quick Timing
```python
import timeit

# Time a simple statement
timeit.timeit('sum(range(1000))', number=1000)

# Time with setup
timeit.timeit('func()', setup='from __main__ import func', number=1000)
```

### 2. cProfile - Detailed Profiling
```python
import cProfile
import pstats

# Profile specific function
cProfile.run('my_function()', 'output.stats')

# Analyze results
with open('output.stats', 'r') as f:
    stats = pstats.Stats(f)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
```

### 3. line_profiler - Line-by-line Analysis
```python
# Install: pip install line_profiler

from line_profiler import LineProfiler

profiler = LineProfiler()

@profiler  # Decorator
def my_function():
    # Your code here
    pass

my_function()
profiler.print_stats()
```

### 4. memory_profiler - Memory Usage
```python
# Install: pip install memory_profiler

from memory_profiler import profile

@profile
def my_function():
    # Your code here
    pass
```

## Optimization Workflow

### Step 1: Static Code Analysis
1. Review code for obvious inefficiencies
2. Check data structure choices
3. Identify potential algorithm improvements
4. Look for unnecessary computations

### Step 2: Baseline Performance Measurement
```python
import time

start = time.time()
result = function_to_test()
elapsed = time.time() - start
print(f"Execution time: {elapsed:.4f} seconds")
```

### Step 3: Identify Bottlenecks
- Use cProfile to find slowest functions
- Use line_profiler for detailed analysis
- Focus on hot paths (most frequently executed code)

### Step 4: Implement Optimizations
- Start with algorithmic improvements (biggest impact)
- Then optimize data structures
- Finally, micro-optimizations

### Step 5: Verify Improvements
- Re-run performance tests
- Ensure correctness is maintained
- Check for any regressions

## Optimization Report Template

When checking code efficiency, provide:

1. **Performance Summary**
   - Overall execution time
   - Memory usage
   - Bottleneck identification

2. **Issues Found**
   - List of inefficiencies
   - Severity rating (High/Medium/Low)
   - Location in code

3. **Optimization Suggestions**
   - Specific code changes
   - Expected performance improvement
   - Trade-offs (if any)

4. **Before/After Comparison**
   - Code snippets showing changes
   - Performance metrics comparison

## Best Practices

1. **Premature Optimization**
   - Don't optimize without profiling first
   - Focus on readability unless performance is critical
   - Use appropriate data structures from the start

2. **Algorithm Selection**
   - Choose O(n log n) over O(n²) for large datasets
   - Consider space-time trade-offs
   - Use built-in functions (usually optimized in C)

3. **Caching and Memoization**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def expensive_function(arg):
       # Expensive computation
       return result
   ```

4. **Lazy Evaluation**
   ```python
   # Use generators for large datasets
   def process_large_file(filename):
       with open(filename) as f:
           for line in f:  # Lazy loading
               yield process_line(line)
   ```

## Example Usage

When invoked after code modification, this skill will:

1. Analyze the code for common inefficiencies
2. Suggest specific optimizations with code examples
3. Provide performance comparison where applicable
4. Generate a summary report of findings

Always remember: "Make it work, make it right, make it fast" - in that order!
