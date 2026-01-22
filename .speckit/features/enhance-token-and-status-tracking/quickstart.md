# Quickstart: 增强 Token 和状态追踪系统

## 概述

本功能增强了 Token 管理和账号状态追踪能力：
1. 支持 `refresh_token` 存储和自动刷新
2. 分离邀请状态 (`invitation_status`) 和入库状态 (`storage_status`)
3. 自动检测账号入库状态，避免重复入库

## 快速开始

### 1. 数据迁移

运行迁移脚本升级现有数据：

```bash
python scripts/migrate_tracker.py
```

### 2. Token 管理

Token 刷新会自动进行，无需手动干预。

手动检查 token 状态：

```python
from src.auth.token_manager import is_token_expired

# 检查是否需要刷新
if is_token_expired(team["token_expires_at"]):
    # 自动刷新
    pass
```

### 3. 入库状态查询

```python
from src.core.storage_manager import check_account_stored

# 查询 CRS 入库状态
result = check_account_stored("user@example.com", "crs")
if result["exists"]:
    print(f"已入库，ID: {result['account_id']}")
```

## 配置说明

### team.json 新字段

| 字段 | 说明 |
|------|------|
| refresh_token | OAuth 刷新令牌 |
| token_expires_at | 过期时间戳 |

### team_tracker.json 新字段

| 字段 | 说明 |
|------|------|
| invitation_status | 邀请状态（原 status） |
| storage_status | 入库状态对象 |
