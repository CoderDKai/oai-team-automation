# Data Model: 增强 Token 和状态追踪系统

**Date**: 2026-01-22
**Feature**: enhance-token-and-status-tracking

## 1. 实体概览

| 实体 | 描述 | 存储位置 |
|------|------|----------|
| TeamConfig | Team 配置信息（含 Token） | team.json |
| AccountTracker | 账号追踪记录 | team_tracker.json |
| StorageStatus | 入库状态 | team_tracker.json (嵌套) |

## 2. TeamConfig 实体

### 2.1 旧格式 (Format 1)

```json
{
  "user": {
    "id": "string",
    "email": "string",
    "idp": "string"
  },
  "account": {
    "id": "string",
    "organizationId": "string",
    "planType": "string"
  },
  "accessToken": "string",
  "refreshToken": "string | null",
  "tokenExpiresAt": "integer | null",
  "authProvider": "string"
}
```

### 2.2 新格式 (Format 2/3)

```json
{
  "account": "string (email)",
  "password": "string",
  "access_token": "string | null",
  "refresh_token": "string | null",
  "token_expires_at": "integer | null",
  "authorized": "boolean",
  "account_id": "string",
  "expires_at": "integer",
  "can_receive_verification_code": "boolean"
}
```

### 2.3 字段说明

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| access_token | string | 否 | 访问令牌 |
| refresh_token | string | 否 | 刷新令牌（来自 OAuth） |
| token_expires_at | integer | 否 | Token 过期时间戳 |

### 2.4 验证规则

- `access_token`: JWT 格式，以 "eyJ" 开头
- `refresh_token`: JWT 格式，以 "eyJ" 开头
- `token_expires_at`: Unix 时间戳，必须大于当前时间

## 3. AccountTracker 实体

### 3.1 数据结构

```json
{
  "teams": {
    "<team_name>": [AccountRecord]
  },
  "last_updated": "string (datetime)"
}
```

### 3.2 AccountRecord 结构

```json
{
  "email": "string",
  "password": "string",
  "invitation_status": "string (enum)",
  "storage_status": StorageStatus,
  "role": "string (enum)",
  "created_at": "string (datetime)",
  "updated_at": "string (datetime)"
}
```

### 3.3 字段说明

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| email | string | 是 | 账号邮箱 |
| password | string | 是 | 账号密码 |
| invitation_status | enum | 是 | 邀请状态 |
| storage_status | object | 否 | 入库状态 |
| role | enum | 是 | 角色 (owner/member) |
| created_at | datetime | 是 | 创建时间 |
| updated_at | datetime | 是 | 更新时间 |

### 3.4 invitation_status 枚举值

| 值 | 描述 |
|-----|------|
| invited | 已发送邀请邮件 |
| registered | 账号已注册并接受邀请 |
| authorized | 账号已完成 OAuth 授权 |
| completed | 账号已完成所有设置（含入库） |
| team_owner | Team Owner（旧格式专用） |

### 3.5 role 枚举值

| 值 | 描述 |
|-----|------|
| owner | Team 管理员 |
| member | Team 成员 |

## 4. StorageStatus 实体

### 4.1 数据结构

```json
{
  "crs": ProviderStatus,
  "cpa": ProviderStatus,
  "s2a": ProviderStatus
}
```

### 4.2 ProviderStatus 结构

```json
{
  "status": "string (enum)",
  "stored_at": "string (datetime) | null",
  "verified_at": "string (datetime) | null",
  "last_check": "string (datetime) | null",
  "account_id": "string | null"
}
```

### 4.3 storage_status.status 枚举值

| 值 | 描述 |
|-----|------|
| not_stored | 未入库 |
| storing | 正在入库中 |
| stored | 已入库 |
| failed | 入库失败 |
| disabled | 该服务未启用 |

## 5. 状态转换图

### 5.1 invitation_status 转换

```
invited -> registered -> authorized -> completed
```

### 5.2 storage_status.status 转换

```
not_stored -> storing -> stored
                    \-> failed
```

## 6. 迁移映射

### 6.1 team.json 字段映射

| 旧字段 | 新字段 | 说明 |
|--------|--------|------|
| token | access_token | 重命名 |
| (新增) | refresh_token | OAuth 刷新令牌 |
| (新增) | token_expires_at | 过期时间戳 |

### 6.2 team_tracker.json 字段映射

| 旧字段 | 新字段 | 说明 |
|--------|--------|------|
| status | invitation_status | 重命名 |
| (新增) | storage_status | 入库状态对象 |
