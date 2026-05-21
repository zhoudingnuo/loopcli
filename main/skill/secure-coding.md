---
name: secure-coding
description: 安全编码专家 - 防止 OWASP Top 10 漏洞
triggers:
  - "security"
  - "vulnerability"
  - "OWASP"
  - "漏洞"
  - "安全"
references:
  - https://owasp.org/www-project-top-ten/
  - https://cheatsheetseries.owasp.org/
---

# 安全编码技能

## OWASP Top 10:2021 检查清单

### 1. 注入漏洞
- SQL 注入：使用参数化查询
- NoSQL 注入：验证和清理输入
- 命令注入：避免 shell_exec()，使用安全函数

### 2. 身份验证失败
- 实施多因素认证
- 安全密码策略
- 防止暴力破解

### 3. 数据暴露
- 加密敏感数据（AES-256）
- HTTPS 强制执行
- 安全密钥管理

### 4. XML 外部实体 (XXE)
- 禁用 XML 外部实体
- 使用 JSON 替代

### 5. 访问控制
- 实施基于角色的访问控制
- 服务器端验证
- 默认拒绝

### 6. 安全配置错误
- 删除默认凭据
- 禁用不必要的功能
- 保持系统更新

### 7. 跨站脚本 (XSS)
- 输出编码
- 内容安全策略 (CSP)
- HTTPOnly 标志

### 8. 不安全的反序列化
- 避免反序列化不受信任的数据
- 完整性检查

### 9. 使用已知漏洞组件
- 定期更新依赖
- 扫描漏洞
- 移除未使用的库

### 10. 日志和监控不足
- 实施集中日志记录
- 监控可疑活动
- 事件响应计划

## 代码审查检查点

```python
# ❌ 不安全
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ 安全
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

```javascript
// ❌ 不安全
eval(userInput);

// ✅ 安全
// 避免完全，使用 JSON.parse 或白名单
```

## 工具集成
- npm audit
- Snyk
- OWASP Dependency-Check
- Bandit (Python)
