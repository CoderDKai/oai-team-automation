# Implementation Plan: 增强 Token 和状态追踪系统

**Branch**: `feature/enhance-token-and-status-tracking` | **Date**: 2026-01-22 | **Spec**: [spec.md](../../.speckit/features/enhance-token-and-status-tracking.md)
**Input**: Feature specification from `.speckit/features/enhance-token-and-status-tracking.md`

## Summary

增强 Token 管理和账号状态追踪系统，支持 refresh_token 存储和自动刷新，分离邀请状态和入库状态，实现服务商入库状态的自动检测。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: requests, tomllib/tomli
**Storage**: JSON 文件 (team.json, team_tracker.json)
**Testing**: pytest
**Target Platform**: macOS/Linux/Windows
**Project Type**: CLI 工具
**Performance Goals**: Token 刷新 < 5s，批量查询 < 10s
**Constraints**: 向后兼容现有数据格式
**Scale/Scope**: 支持多 Team、多服务商

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

项目 constitution 为模板状态，无特定约束。设计遵循以下原则：
- 向后兼容：不破坏现有数据格式
- 简单优先：最小化代码变更
- 可测试性：所有新模块可独立测试

## Project Structure

### Documentation (this feature)

```text
.speckit/features/enhance-token-and-status-tracking/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── token-manager.md
│   ├── storage-manager.md
│   └── provider-query.md
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── auth/
│   ├── token_manager.py     # 新建: Token 管理模块
│   ├── crs/client.py        # 修改: 添加查询接口
│   ├── cpa/client.py        # 修改: 添加查询接口
│   └── s2a/client.py        # 修改: 添加查询接口
├── core/
│   ├── config.py            # 修改: 扩展 team.json 解析
│   ├── utils.py             # 修改: 更新 tracker 函数
│   ├── storage_manager.py   # 新建: 入库状态管理
│   └── workflow.py          # 修改: 集成新状态管理
└── cli/

scripts/
└── migrate_tracker.py       # 新建: 数据迁移脚本

tests/
├── test_token_manager.py    # 新建
└── test_storage_manager.py  # 新建
```

**Structure Decision**: 单项目结构，新增模块放在现有目录下

## Complexity Tracking

无 Constitution 违规，无需记录复杂性理由。

## Implementation Phases

### Phase 1: 数据模型扩展

**目标**: 扩展 team.json 和 team_tracker.json 数据结构

**任务**:
1. 修改 `src/core/config.py` 支持新字段解析
2. 修改 `src/core/utils.py` 支持 invitation_status 和 storage_status
3. 创建 `scripts/migrate_tracker.py` 迁移脚本

**依赖**: 无

### Phase 2: Token 管理模块

**目标**: 实现 Token 提取、刷新和更新功能

**任务**:
1. 创建 `src/auth/token_manager.py`
2. 实现 `extract_tokens_from_response()`
3. 实现 `refresh_access_token()`
4. 实现 `is_token_expired()`
5. 实现 `update_team_tokens()`

**依赖**: Phase 1

### Phase 3: 服务商查询接口

**目标**: 为 CRS/CPA/S2A 实现账号查询接口

**任务**:
1. 在 `src/auth/crs/client.py` 添加 `crs_query_account()`
2. 在 `src/auth/cpa/client.py` 添加 `cpa_query_account()`
3. 在 `src/auth/s2a/client.py` 添加 `s2a_query_account()`

**依赖**: 无（可与 Phase 2 并行）

### Phase 4: 入库状态管理

**目标**: 实现入库状态初始化、查询和更新

**任务**:
1. 创建 `src/core/storage_manager.py`
2. 实现 `init_storage_status()`
3. 实现 `check_account_stored()`
4. 实现 `update_storage_status()`
5. 实现 `get_enabled_providers()`

**依赖**: Phase 1, Phase 3

### Phase 5: 集成测试

**目标**: 编写测试并集成到工作流

**任务**:
1. 创建 `tests/test_token_manager.py`
2. 创建 `tests/test_storage_manager.py`
3. 修改 `src/core/workflow.py` 集成新模块

**依赖**: Phase 2, Phase 4

## Key Files

### 需要修改的文件

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| src/core/config.py | 修改 | 扩展 team.json 解析 |
| src/core/utils.py | 修改 | 更新 tracker 函数 |
| src/auth/crs/client.py | 修改 | 添加查询接口 |
| src/auth/cpa/client.py | 修改 | 添加查询接口 |
| src/auth/s2a/client.py | 修改 | 添加查询接口 |
| src/core/workflow.py | 修改 | 集成新模块 |

### 需要创建的文件

| 文件 | 说明 |
|------|------|
| src/auth/token_manager.py | Token 管理模块 |
| src/core/storage_manager.py | 入库状态管理 |
| scripts/migrate_tracker.py | 数据迁移脚本 |
| tests/test_token_manager.py | Token 管理测试 |
| tests/test_storage_manager.py | 入库状态测试 |

## Risk Mitigation

| 风险 | 缓解措施 |
|------|----------|
| Token 刷新失败 | 重试机制（3次），失败通知 |
| 数据迁移损坏 | 迁移前自动备份 |
| 并发写入冲突 | 文件锁 + 原子写入 |

## Next Steps

运行 `/speckit.tasks` 生成详细任务列表。
