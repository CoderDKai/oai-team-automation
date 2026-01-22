# 功能规格说明：增强 Token 和状态追踪系统

## 元数据

- **功能名称**: 增强 Token 和状态追踪系统
- **功能分支**: `feature/enhance-token-and-status-tracking`
- **创建日期**: 2026-01-22
- **状态**: 草稿
- **优先级**: 高

## 1. 功能概述

### 1.1 背景

当前系统在管理 team 和 team 子账号时存在以下问题：

1. **Token 管理不完整**：只存储了 `access_token`（旧格式字段名为 `accessToken`，新格式字段名为 `token`），缺少 `refresh_token` 的存储和管理
2. **状态混淆**：`team_tracker.json` 中的 `status` 字段同时表示邀请状态和入库状态，导致无法准确追踪账号的完整生命周期
3. **入库状态缺失**：无法追踪账号是否已成功添加到中转服务（CRS、CPA、S2A）的账号库中，可能导致账号"空置"（已邀请但未入库）

**Token 来源说明**：
- **旧格式**：`accessToken` 来自 `https://chatgpt.com/api/auth/session` 接口，该接口不返回 `refreshToken`
- **新格式**：`token` 来自登录流程，同样缺少 `refresh_token`
- **refresh_token 来源**：通过 CRS/CPA/S2A 的 OAuth 授权流程获取，目前未保存到 team.json 中

### 1.2 目标

本功能旨在解决上述问题，通过以下改进提升系统的可靠性和可维护性：

1. 完善 Token 管理机制，支持 `access_token` 和 `refresh_token` 的存储和自动刷新
2. 分离邀请状态和入库状态，使状态追踪更加清晰
3. 实现入库状态的自动检测和验证，避免账号空置问题

### 1.3 适用范围

- Team 配置文件（`team.json`）
- Team 追踪文件（`team_tracker.json`）
- 认证系统（CRS、CPA、S2A）
- 自动化测试流程

## Clarifications

### Session 2026-01-22

- Q: Token 字段的语义澄清 - 当前代码中 `token` 和 `accessToken` 字段的实际含义是什么？ → A: 旧格式的 `accessToken` 和新格式的 `token` 都存储的是 access_token，需要新增对应的 refresh_token 字段（旧格式：`refreshToken`，新格式：`refresh_token`）
- Q: 命名规范一致性 - 如何保持字段命名的一致性？ → A: 旧格式（格式1）全部使用驼峰命名（accessToken, refreshToken, tokenExpiresAt），新格式（格式2/3）全部使用下划线命名（access_token, refresh_token, token_expires_at），不混用驼峰和下划线
- Q: 新格式中的 `token` 字段命名 - 是否应该重命名为 `access_token`？ → A: 是的，为了语义清晰，新格式中应将 `token` 字段重命名为 `access_token`，避免歧义
- Q: Token 的来源是什么？ → A: 旧格式的 `accessToken` 来自 `/api/auth/session` 接口（该接口不返回 refreshToken）；`refresh_token` 来自 CRS/CPA/S2A 的 OAuth 授权流程（`codex_data.tokens.refreshToken`），目前未保存到 team.json 中

## 2. 需求分析

### 2.1 功能需求

#### FR-1: Token 管理增强

**需求描述**：在 `team.json` 和 `team_tracker.json` 中增加 `refresh_token` 字段的支持。

**详细说明**：

1. **team.json 格式扩展**
   - 旧格式（驼峰命名）：现有 `accessToken` 字段来自 `/api/auth/session` 接口，新增 `refreshToken` 字段存储 refresh_token（来自 OAuth 授权流程），新增 `tokenExpiresAt` 字段记录过期时间
   - 新格式（下划线命名）：将现有 `token` 字段重命名为 `access_token`，新增 `refresh_token` 字段，新增 `token_expires_at` 字段记录过期时间

2. **Token 获取来源**
   - `access_token`：旧格式从 `/api/auth/session` 获取，新格式从登录流程获取
   - `refresh_token`：从 CRS/CPA/S2A 的 OAuth 授权流程中获取（`codex_data.tokens.refreshToken`）
   - 在 OAuth 授权完成后，将 `refresh_token` 保存到 team.json 中

3. **登录流程修改**
   - 在账号登录成功后，从 API 响应中提取 `access_token`
   - 在 OAuth 授权完成后，从授权响应中提取 `refresh_token`
   - 将两个 token 同时保存到配置文件中
   - 记录 token 的过期时间

3. **Token 刷新机制**
   - 在 token 即将过期时（如剩余时间少于 1 小时），自动使用 `refresh_token` 刷新
   - 刷新成功后更新 `access_token`、`refresh_token` 和过期时间
   - 刷新失败时标记账号需要重新登录

**验收标准**：
- [ ] `team.json` 中所有账号都包含 `refresh_token` 字段
- [ ] 登录流程能正确提取并保存两个 token
- [ ] Token 刷新机制能自动运行且成功率 > 95%

#### FR-2: 状态字段重构

**需求描述**：将 `team_tracker.json` 中的 `status` 字段重命名为 `invitation_status`，专门用于追踪邀请状态。

**详细说明**：

1. **字段重命名**
   - 将现有的 `status` 字段重命名为 `invitation_status`
   - 保持原有的状态值不变：`invited` → `registered` → `authorized` → `completed`

2. **状态含义明确化**
   - `invited`: 已发送邀请邮件
   - `registered`: 账号已注册并接受邀请
   - `authorized`: 账号已完成授权（OAuth 流程）
   - `completed`: 账号已完成所有设置（包括入库）

3. **向后兼容**
   - 提供迁移脚本，自动将旧的 `status` 字段转换为 `invitation_status`
   - 在加载 `team_tracker.json` 时自动检测并转换旧格式

**验收标准**：
- [ ] 所有代码中的 `status` 引用都已更新为 `invitation_status`
- [ ] 迁移脚本能正确转换现有的追踪文件
- [ ] 旧格式文件能自动兼容并转换

#### FR-3: 入库状态管理

**需求描述**：在 `team_tracker.json` 中增加 `storage_status` 字段，分别记录账号在各个中转服务中的入库状态。

**详细说明**：

1. **数据结构设计**
   ```json
   {
     "email": "account@example.com",
     "password": "password",
     "invitation_status": "authorized",
     "storage_status": {
       "crs": {
         "status": "stored",
         "stored_at": "2026-01-22 15:30:00",
         "verified_at": "2026-01-22 15:35:00",
         "account_id": "crs_account_123"
       },
       "cpa": {
         "status": "not_stored",
         "last_check": "2026-01-22 15:30:00"
       },
       "s2a": {
         "status": "disabled"
       }
     },
     "role": "member",
     "created_at": "2026-01-22 14:30:00",
     "updated_at": "2026-01-22 15:35:00"
   }
   ```

2. **状态值定义**
   - `not_stored`: 未入库
   - `storing`: 正在入库中
   - `stored`: 已入库
   - `failed`: 入库失败
   - `disabled`: 该服务未启用

3. **入库状态检测**
   - 在执行入库操作前，先调用各服务商的查询接口检查账号是否已存在
   - 如果账号已存在，更新 `storage_status` 为 `stored`，跳过入库操作
   - 如果账号不存在，执行入库操作并更新状态

**验收标准**：
- [ ] `team_tracker.json` 中所有账号都包含 `storage_status` 字段
- [ ] 入库前能正确检测账号是否已存在
- [ ] 避免重复入库，减少 API 调用次数

#### FR-4: 服务商查询接口集成

**需求描述**：为每个中转服务（CRS、CPA、S2A）实现账号查询接口，用于检测账号是否已入库。

**详细说明**：

1. **CRS 查询接口**
   - API 端点：`GET {CRS_API_BASE}/admin/openai-accounts?email={email}`
   - 返回账号列表，根据 email 匹配判断是否已入库
   - 提取账号 ID 并保存到 `storage_status.crs.account_id`

2. **CPA 查询接口**
   - API 端点：`GET {CPA_API_BASE}/api/accounts?search={email}`
   - 返回账号列表，根据 email 匹配判断是否已入库
   - 提取账号 ID 并保存到 `storage_status.cpa.account_id`

3. **S2A 查询接口**
   - API 端点：`GET {S2A_API_BASE}/api/accounts?email={email}`
   - 返回账号列表，根据 email 匹配判断是否已入库
   - 提取账号 ID 并保存到 `storage_status.s2a.account_id`

4. **查询时机**
   - 在执行入库操作前自动查询
   - 提供手动查询命令，用于批量验证入库状态
   - 在账号授权完成后自动查询一次

**验收标准**：
- [ ] 三个服务商的查询接口都已实现
- [ ] 查询结果能正确解析并更新到 `storage_status`
- [ ] 查询失败时有适当的错误处理和重试机制

### 2.2 非功能需求

#### NFR-1: 性能要求

- Token 刷新操作应在 5 秒内完成
- 入库状态查询应支持批量操作，单次查询不超过 10 秒
- 文件读写操作应使用锁机制，避免并发冲突

#### NFR-2: 可靠性要求

- Token 刷新失败时应有重试机制（最多 3 次）
- 入库状态查询失败不应影响主流程继续执行
- 所有状态变更都应记录日志，便于问题排查

#### NFR-3: 兼容性要求

- 必须向后兼容现有的 `team.json` 和 `team_tracker.json` 格式
- 提供自动迁移脚本，无需手动修改配置文件
- 支持渐进式升级，旧版本数据能自动转换

#### NFR-4: 可维护性要求

- 代码应遵循现有的项目规范和风格
- 关键函数应有完整的文档字符串
- 状态转换逻辑应清晰可追踪

## 3. 技术设计

### 3.1 数据模型变更

#### 3.1.1 team.json 格式扩展

**旧格式（格式1）**：
> 注：`accessToken` 来自 `/api/auth/session` 接口，`refreshToken` 需从 OAuth 授权流程获取

```json
{
  "user": {"id": "user-xxx", "email": "your-email@example.com", "idp": "auth0"},
  "account": {"id": "xxx", "organizationId": "org-xxx", "planType": "team"},
  "accessToken": "eyJhbGciOiJSUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJSUzI1NiIs...",  // 新增，来自 OAuth 授权流程
  "tokenExpiresAt": 1737561600,  // 新增
  "authProvider": "openai"
}
```

**新格式（格式2/3）**：
> 注：将 `token` 重命名为 `access_token`，`refresh_token` 需从 OAuth 授权流程获取

```json
{
  "account": "team-owner@example.com",
  "password": "YourPassword@2025",
  "access_token": "eyJhbGciOiJSUzI1NiIs...",  // 原 token 字段重命名
  "refresh_token": "eyJhbGciOiJSUzI1NiIs...",  // 新增，来自 OAuth 授权流程
  "token_expires_at": 1737561600,  // 新增
  "authorized": false,
  "account_id": "",
  "expires_at": 0,
  "can_receive_verification_code": true
}
```

#### 3.1.2 team_tracker.json 格式扩展

**旧格式**：
```json
{
  "teams": {
    "team_name": [
      {
        "email": "account@example.com",
        "password": "password",
        "status": "authorized",
        "role": "member",
        "created_at": "2025-01-22 14:30:00",
        "updated_at": "2025-01-22 14:30:00"
      }
    ]
  },
  "last_updated": "2025-01-22 14:30:00"
}
```

**新格式**：
```json
{
  "teams": {
    "team_name": [
      {
        "email": "account@example.com",
        "password": "password",
        "invitation_status": "authorized",
        "storage_status": {
          "crs": {
            "status": "stored",
            "stored_at": "2026-01-22 15:30:00",
            "verified_at": "2026-01-22 15:35:00",
            "account_id": "crs_account_123"
          },
          "cpa": {
            "status": "not_stored",
            "last_check": "2026-01-22 15:30:00"
          },
          "s2a": {
            "status": "disabled"
          }
        },
        "role": "member",
        "created_at": "2025-01-22 14:30:00",
        "updated_at": "2026-01-22 15:35:00"
      }
    ]
  },
  "last_updated": "2026-01-22 15:35:00"
}
```

### 3.2 核心模块设计

#### 3.2.1 Token 管理模块

**位置**：`src/auth/token_manager.py`（新建）

**核心功能**：
1. `extract_tokens_from_response(response: dict) -> dict`
   - 从登录 API 响应中提取 access_token 和 refresh_token
   - 计算并返回 token 过期时间

2. `refresh_access_token(refresh_token: str) -> dict`
   - 使用 refresh_token 刷新 access_token
   - 返回新的 token 信息

3. `is_token_expired(expires_at: int) -> bool`
   - 检查 token 是否已过期或即将过期（1小时内）

4. `update_team_tokens(team_name: str, tokens: dict) -> None`
   - 更新 team.json 中的 token 信息

#### 3.2.2 入库状态管理模块

**位置**：`src/core/storage_manager.py`（新建）

**核心功能**：
1. `init_storage_status() -> dict`
   - 初始化 storage_status 结构
   - 根据配置文件判断哪些服务商已启用

2. `check_account_stored(email: str, provider: str) -> dict`
   - 查询账号在指定服务商中的入库状态
   - 返回 {status, account_id, last_check}

3. `update_storage_status(tracker: dict, team: str, email: str, provider: str, status_data: dict) -> None`
   - 更新 team_tracker.json 中的入库状态

4. `get_enabled_providers() -> list[str]`
   - 从配置文件读取已启用的服务商列表

#### 3.2.3 服务商查询接口模块

**CRS 查询接口**（位置：`src/auth/crs/client.py`）

新增函数：
```python
def crs_query_account(email: str) -> dict:
    """查询账号是否已在 CRS 中入库

    Returns:
        {
            "exists": bool,
            "account_id": str | None,
            "account_data": dict | None
        }
    """
```

**CPA 查询接口**（位置：`src/auth/cpa/client.py`）

新增函数：
```python
def cpa_query_account(email: str) -> dict:
    """查询账号是否已在 CPA 中入库

    Returns:
        {
            "exists": bool,
            "account_id": str | None,
            "account_data": dict | None
        }
    """
```

**S2A 查询接口**（位置：`src/auth/s2a/client.py`）

新增函数：
```python
def s2a_query_account(email: str) -> dict:
    """查询账号是否已在 S2A 中入库

    Returns:
        {
            "exists": bool,
            "account_id": str | None,
            "account_data": dict | None
        }
    """
```

### 3.3 工作流程设计

#### 3.3.1 登录流程增强

```
1. 用户输入账号密码
2. 调用登录 API
3. 从响应中提取 access_token 和 refresh_token
4. 计算 token 过期时间
5. 保存 token 信息到 team.json
6. 更新 invitation_status 为 "registered"
```

#### 3.3.2 Token 刷新流程

```
1. 检查 token 是否即将过期（剩余时间 < 1小时）
2. 如果即将过期，使用 refresh_token 调用刷新 API
3. 提取新的 access_token 和 refresh_token
4. 更新 team.json 中的 token 信息
5. 如果刷新失败，标记账号需要重新登录
```

#### 3.3.3 入库流程增强

```
1. 检查 invitation_status 是否为 "authorized"
2. 获取已启用的服务商列表
3. 对每个服务商：
   a. 检查 storage_status 是否已为 "stored"
   b. 如果未入库，调用查询接口检查账号是否存在
   c. 如果账号已存在，更新 storage_status 为 "stored"
   d. 如果账号不存在，执行入库操作
   e. 入库成功后，更新 storage_status 为 "stored"
4. 所有服务商都入库成功后，更新 invitation_status 为 "completed"
```

## 4. 实现计划

### 4.1 阶段划分

#### 阶段 1：数据模型扩展（优先级：高）

**任务清单**：
- [ ] 创建数据迁移脚本 `scripts/migrate_tracker.py`
- [ ] 扩展 `team.json` 解析逻辑，支持 refresh_token 字段
- [ ] 扩展 `team_tracker.json` 数据结构
- [ ] 实现向后兼容的加载逻辑

**预计工作量**：2-3 天

**依赖关系**：无

#### 阶段 2：Token 管理模块（优先级：高）

**任务清单**：
- [ ] 创建 `src/auth/token_manager.py` 模块
- [ ] 实现 token 提取和刷新逻辑
- [ ] 修改登录流程，集成 token 管理
- [ ] 添加 token 过期检查和自动刷新
- [ ] 编写单元测试

**预计工作量**：3-4 天

**依赖关系**：阶段 1

#### 阶段 3：服务商查询接口（优先级：高）

**任务清单**：
- [ ] 在 `src/auth/crs/client.py` 中实现 `crs_query_account()`
- [ ] 在 `src/auth/cpa/client.py` 中实现 `cpa_query_account()`
- [ ] 在 `src/auth/s2a/client.py` 中实现 `s2a_query_account()`
- [ ] 添加错误处理和重试机制
- [ ] 编写单元测试

**预计工作量**：2-3 天

**依赖关系**：无（可与阶段 2 并行）

#### 阶段 4：入库状态管理（优先级：高）

**任务清单**：
- [ ] 创建 `src/core/storage_manager.py` 模块
- [ ] 实现入库状态初始化和更新逻辑
- [ ] 修改入库流程，集成状态检测
- [ ] 实现批量状态验证功能
- [ ] 编写单元测试

**预计工作量**：3-4 天

**依赖关系**：阶段 1、阶段 3

#### 阶段 5：集成测试和文档（优先级：中）

**任务清单**：
- [ ] 编写集成测试用例
- [ ] 更新用户文档和 README
- [ ] 创建迁移指南
- [ ] 进行端到端测试

**预计工作量**：2-3 天

**依赖关系**：阶段 2、阶段 4

### 4.2 关键文件清单

**需要修改的文件**：
- `src/core/config.py` - 扩展 team.json 解析逻辑
- `src/core/utils.py` - 更新 tracker 相关函数
- `src/core/workflow.py` - 集成新的状态管理
- `src/auth/crs/client.py` - 添加查询接口
- `src/auth/cpa/client.py` - 添加查询接口
- `src/auth/s2a/client.py` - 添加查询接口

**需要创建的文件**：
- `src/auth/token_manager.py` - Token 管理模块
- `src/core/storage_manager.py` - 入库状态管理模块
- `scripts/migrate_tracker.py` - 数据迁移脚本
- `tests/test_token_manager.py` - Token 管理测试
- `tests/test_storage_manager.py` - 入库状态管理测试

## 5. 测试策略

### 5.1 单元测试

#### Token 管理模块测试
- [ ] 测试 token 提取功能
- [ ] 测试 token 刷新功能
- [ ] 测试 token 过期检查
- [ ] 测试错误处理和重试机制

#### 入库状态管理测试
- [ ] 测试状态初始化
- [ ] 测试状态更新
- [ ] 测试批量查询
- [ ] 测试服务商查询接口

### 5.2 集成测试

- [ ] 测试完整的登录到入库流程
- [ ] 测试 token 自动刷新机制
- [ ] 测试多服务商并行入库
- [ ] 测试数据迁移脚本

### 5.3 兼容性测试

- [ ] 测试旧格式 team.json 的加载
- [ ] 测试旧格式 team_tracker.json 的迁移
- [ ] 测试混合格式的处理

## 6. 风险评估与缓解措施

### 6.1 技术风险

#### 风险 1：Token 刷新失败导致服务中断

**风险等级**：高

**影响**：账号无法正常使用，影响自动化流程

**缓解措施**：
- 实现重试机制（最多 3 次）
- 刷新失败时发送通知
- 提供手动刷新命令
- 记录详细的错误日志

#### 风险 2：数据迁移导致配置文件损坏

**风险等级**：高

**影响**：现有配置丢失，需要手动恢复

**缓解措施**：
- 迁移前自动备份原文件
- 提供回滚机制
- 充分测试迁移脚本
- 提供数据验证工具

#### 风险 3：服务商查询接口变更

**风险等级**：中

**影响**：无法正确查询入库状态

**缓解措施**：
- 使用版本化的 API 端点
- 实现接口兼容性检测
- 提供降级方案（跳过查询，直接入库）
- 监控 API 变更通知

### 6.2 运维风险

#### 风险 4：并发访问导致数据不一致

**风险等级**：中

**影响**：多个进程同时修改配置文件，导致数据覆盖

**缓解措施**：
- 使用文件锁机制
- 实现原子性写入
- 添加数据版本号
- 提供冲突检测和解决机制

## 7. 附录

### 7.1 术语表

| 术语 | 定义 |
|------|------|
| access_token | 访问令牌，用于 API 认证 |
| refresh_token | 刷新令牌，用于获取新的 access_token |
| invitation_status | 邀请状态，追踪账号从邀请到授权的流程 |
| storage_status | 入库状态，追踪账号在各服务商中的入库情况 |
| CRS | Codex 授权系统 |
| CPA | Codex/Copilot Authorization |
| S2A | Sub2API OAuth 认证系统 |

### 7.2 状态转换图

#### 邀请状态转换
```
invited → registered → authorized → completed
```

#### 入库状态转换
```
not_stored → storing → stored
           ↓
         failed
```

### 7.3 配置示例

#### 完整的 team.json 示例（新格式）
```json
{
  "account": "team-owner@example.com",
  "password": "YourPassword@2025",
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_expires_at": 1737561600,
  "authorized": true,
  "account_id": "acc_123456",
  "expires_at": 0,
  "can_receive_verification_code": true
}
```

#### 完整的 team_tracker.json 示例（新格式）
```json
{
  "teams": {
    "my_team": [
      {
        "email": "member1@example.com",
        "password": "Password123",
        "invitation_status": "completed",
        "storage_status": {
          "crs": {
            "status": "stored",
            "stored_at": "2026-01-22 15:30:00",
            "verified_at": "2026-01-22 15:35:00",
            "account_id": "crs_acc_001"
          },
          "cpa": {
            "status": "stored",
            "stored_at": "2026-01-22 15:32:00",
            "verified_at": "2026-01-22 15:36:00",
            "account_id": "cpa_acc_001"
          },
          "s2a": {
            "status": "disabled"
          }
        },
        "role": "member",
        "created_at": "2026-01-22 14:30:00",
        "updated_at": "2026-01-22 15:36:00"
      }
    ]
  },
  "last_updated": "2026-01-22 15:36:00"
}
```

### 7.4 参考资料

- 现有代码库文档
- OpenAI API 文档
- CRS/CPA/S2A 服务商 API 文档
- OAuth 2.0 规范

### 7.5 变更历史

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-01-22 | System | 初始版本 |

---

**文档结束**
