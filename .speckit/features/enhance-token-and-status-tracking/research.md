# Research: 增强 Token 和状态追踪系统

**Date**: 2026-01-22
**Feature**: enhance-token-and-status-tracking

## 1. Token 刷新机制研究

### 1.1 OpenAI OAuth Token 刷新

**Decision**: 使用标准 OAuth 2.0 refresh_token 流程刷新 access_token

**Rationale**:
- CRS/CPA/S2A 的 OAuth 授权流程返回 `refresh_token`
- 当前代码中 `crs_exchange_code()` 已经获取到 `refreshToken`（见 `src/auth/crs/client.py:199`）
- S2A 的 `s2a_add_account()` 也支持 `refresh_token` 参数（见 `src/auth/s2a/client.py:371`）

**Alternatives considered**:
- 重新登录获取新 token：用户体验差，需要人工干预
- 使用长期有效 token：安全风险高，不符合 OAuth 最佳实践

### 1.2 Token 过期时间计算

**Decision**: 使用 `expires_in` 字段计算过期时间戳

**Rationale**:
- CRS 返回的 `codex_data.tokens.expires_in` 默认为 864000 秒（10天）
- 计算公式：`token_expires_at = current_timestamp + expires_in`
- 提前 1 小时刷新，避免 token 在使用过程中过期

**Alternatives considered**:
- 固定过期时间：不够灵活，不同服务商可能有不同的过期策略
- 每次请求前检查：性能开销大，不必要

## 2. 服务商查询接口研究

### 2.1 CRS 账号查询

**Decision**: 使用现有的 `crs_get_accounts()` 函数，通过 email 匹配

**Rationale**:
- 已有实现：`src/auth/crs/client.py:251-274`
- API 端点：`GET {CRS_API_BASE}/admin/openai-accounts`
- 返回所有账号列表，通过 `name` 字段（存储 email）匹配

**Implementation notes**:
- 现有 `crs_check_account_exists()` 函数可直接复用
- 需要扩展返回账号 ID 和详细信息

### 2.2 CPA 账号查询

**Decision**: 需要新增查询接口

**Rationale**:
- 当前 CPA 模块没有账号查询功能
- CPA 后台自动处理入库，但需要验证入库状态
- 需要调研 CPA API 是否支持账号查询

**Implementation notes**:
- 可能的 API 端点：`GET {CPA_API_BASE}/v0/management/accounts`
- 需要确认 API 文档或通过测试验证

### 2.3 S2A 账号查询

**Decision**: 使用现有的 `s2a_get_accounts()` 函数

**Rationale**:
- 已有实现：`src/auth/s2a/client.py:424-450`
- API 端点：`GET {S2A_API_BASE}/admin/accounts`
- 支持按 platform 过滤

**Implementation notes**:
- 现有 `s2a_check_account_exists()` 函数可直接复用
- 需要扩展返回账号 ID 和详细信息

## 3. 数据迁移策略研究

### 3.1 team.json 迁移

**Decision**: 向后兼容，自动检测格式并转换

**Rationale**:
- 现有代码已支持多格式检测（见 `src/core/config.py:126-181`）
- 新增字段使用可选方式，不破坏现有格式
- 读取时自动补充默认值

**Migration strategy**:
1. 读取时检测格式（旧格式/新格式）
2. 旧格式：`accessToken` -> 保持，新增 `refreshToken`、`tokenExpiresAt`
3. 新格式：`token` -> 重命名为 `access_token`，新增 `refresh_token`、`token_expires_at`
4. 写入时保持原格式的命名规范

### 3.2 team_tracker.json 迁移

**Decision**: 提供迁移脚本，支持自动转换

**Rationale**:
- `status` 字段重命名为 `invitation_status`
- 新增 `storage_status` 复合字段
- 需要保留历史数据

**Migration strategy**:
1. 备份原文件
2. 遍历所有账号记录
3. `status` -> `invitation_status`
4. 初始化 `storage_status` 为空对象（后续查询填充）
5. 保存新格式文件

## 4. 并发安全研究

### 4.1 文件锁机制

**Decision**: 使用 `fcntl` 文件锁（Unix）或 `msvcrt`（Windows）

**Rationale**:
- 多进程可能同时修改 team.json 和 team_tracker.json
- 需要防止数据覆盖和损坏

**Implementation notes**:
- 使用上下文管理器封装锁操作
- 读写操作都需要加锁
- 超时机制防止死锁

### 4.2 原子性写入

**Decision**: 写入临时文件后重命名

**Rationale**:
- 防止写入过程中断导致文件损坏
- 重命名操作在大多数文件系统上是原子的

**Implementation notes**:
```python
# 写入临时文件
with open(f"{filepath}.tmp", "w") as f:
    json.dump(data, f)
# 原子重命名
os.replace(f"{filepath}.tmp", filepath)
```

## 5. 技术栈确认

| 项目 | 值 |
|------|-----|
| Language/Version | Python 3.11+ |
| Primary Dependencies | requests, tomllib/tomli |
| Storage | JSON 文件 (team.json, team_tracker.json) |
| Testing | pytest |
| Target Platform | macOS/Linux/Windows |
| Project Type | CLI 工具 |

## 6. 未解决问题

### 6.1 CPA 账号查询 API

**Status**: 需要确认

**Action**: 测试 CPA API 是否支持账号列表查询，或联系 CPA 服务提供方确认

### 6.2 Token 刷新 API 端点

**Status**: 需要确认

**Action**: 确认各服务商的 token 刷新 API 端点：
- CRS: 可能是 `POST /admin/openai-accounts/{id}/refresh`
- S2A: 可能是 `POST /admin/accounts/{id}/refresh`

## 7. 结论

所有主要技术问题已有解决方案：
1. Token 管理：使用标准 OAuth 刷新流程
2. 服务商查询：CRS 和 S2A 已有接口，CPA 需要新增
3. 数据迁移：向后兼容 + 迁移脚本
4. 并发安全：文件锁 + 原子写入

可以进入 Phase 1 设计阶段。
