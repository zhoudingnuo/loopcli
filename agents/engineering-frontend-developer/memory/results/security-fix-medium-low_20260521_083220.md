# 安全审计 Medium x3 + Low x2 残留问题修复报告

## 修复时间
2026-05-21 08:32:20

## 修复项

### Medium #1: CORS 默认策略过于宽松
- **文件**: `webui/server.py`
- **修复**: CORS_ORIGINS 未配置环境变量时，默认从 `*` 改为 `["http://localhost:3000"]`
- **变更**: 新增 `_raw_cors` 变量处理逻辑，空值时使用安全默认值

### Medium #2: write_json 并发竞态
- **文件**: `webui/server.py`
- **修复**: 新增 `_json_lock = threading.Lock()`，`write_json` 函数内加锁保护
- **变更**: 所有 `write_json` 调用自动获得线程安全保护

### Medium #3: 消息文件名冲突
- **文件**: `webui/server.py`
- **修复**: 引入 `uuid` 模块，inbox 消息文件名加入 8 位随机 hex 后缀
- **变更**: `webui_{ts}.md` → `webui_{ts}_{uuid4().hex[:8]}.md`

### Low #1: 默认绑定 0.0.0.0
- **文件**: `webui/server.py`
- **修复**: `main()` 中默认 host 从 `"0.0.0.0"` 改为 `"127.0.0.1"`
- **变更**: 支持 `LOOPCLI_HOST` 环境变量覆盖

### Low #2: git add -A 宽泛操作
- **文件**: `run.py`
- **修复**: `git_push()` 中 `git add -A` 替换为 `git add memory/ log/ inbox/`
- **变更**: 只 stage Agent 数据目录，避免意外提交敏感文件

## 测试结果
- 79 tests passed, 0 failed
- 新增 2 个 CORS 测试用例（验证配置 origin 放行、未知 origin 拒绝）
