---
name: test-driven-development
description: TDD 专家 - 测试驱动开发工作流
triggers:
  - "TDD"
  - "test"
  - "testing"
  - "单元测试"
  - "测试驱动"
---

# 测试驱动开发技能

## TDD 循环

### 红-绿-重构
1. **红**：编写失败的测试
2. **绿**：编写最少代码使测试通过
3. **重构**：改进代码质量
4. 重复

## 测试层次

### 1. 单元测试
- 测试单个函数/方法
- 快速执行（毫秒级）
- 隔离依赖

### 2. 集成测试
- 测试组件交互
- 中等速度
- 真实依赖

### 3. 端到端测试
- 测试用户流程
- 较慢速度
- 真实环境

## 测试覆盖率目标

| 类型 | 覆盖率目标 |
|------|-----------|
| 核心业务逻辑 | 90%+ |
| API 端点 | 80%+ |
| UI 组件 | 70%+ |
| 工具函数 | 95%+ |

## 最佳实践

```python
# 测试结构：AAA 模式
def test_user_authentication():
    # Arrange（准备）
    user = create_user(email="test@example.com", password="secure123")
    login_data = {"email": "test@example.com", "password": "secure123"}

    # Act（执行）
    result = authenticate_user(login_data)

    # Assert（断言）
    assert result.is_authenticated == True
    assert result.token is not None
```

## Mock 和 Stub

- **Mock**：验证行为
- **Stub**：提供测试数据
- **Spy**：记录调用

## 工具推荐

- Python: pytest, unittest, mock
- JavaScript: Jest, Vitest, MSW
- Go: testing 包
