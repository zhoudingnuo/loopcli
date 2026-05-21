---
name: debug-systematic
description: 系统化调试 - 结构化问题解决
triggers:
  - "debug"
  - "error"
  - "bug"
  - "调试"
  - "故障"
---

# 系统化调试技能

## 调试协议

### 第一步：定义问题
- [ ] 具体错误消息
- [ ] 预期行为
- [ ] 实际行为
- [ ] 复现步骤

### 第二步：收集信息
```bash
# 日志级别调整
DEBUG=1
VERBOSE=1

# 启用详细输出
python -m traceback
node --trace-warnings
```

### 第三步：形成假设
- 最可能的原因是什么？
- 最近有什么变化？
- 这与已知问题模式匹配吗？

### 第四步：验证假设
- 添加日志/断点
- 最小化复现
- 二分搜索（git bisect）

### 第五步：修复和验证
- [ ] 修复根本原因（非症状）
- [ ] 添加测试防止回归
- [ ] 文档化

## 调试工具箱

### Python
```python
import pdb; pdb.set_trace()  # 断点
import logging
logging.basicConfig(level=logging.DEBUG)
```

### JavaScript
```javascript
console.trace()  // 堆栈跟踪
debugger;        // 断点
```

### 日志模式
```python
logger.debug(f"Processing user {user_id}, balance: {balance}")
logger.error(f"Payment failed: {error}", exc_info=True)
```

## 常见模式

### 零点隔离
- 代码最近工作正常 → 变更了什么？
- 只在特定环境失败 → 环境差异
- 随机失败 → 竞态条件

### 橡皮鸭调试
1. 向橡皮鸭（或同事）解释代码
2. 在解释中发现问题
3. 修复

## 性能调试
```bash
# Python
python -m cProfile script.py

# Node.js
node --prof script.js
node --prof-process isolate-*.log > processed.txt
```
