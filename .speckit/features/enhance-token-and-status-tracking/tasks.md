# Tasks: 增强 Token 和状态追踪系统

**Input**: Design documents from `.speckit/features/enhance-token-and-status-tracking/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: 测试任务已包含（规格说明中要求单元测试和集成测试）

**Organization**: 任务按功能需求（FR）组织，每个 FR 可独立实现和测试。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 任务所属的功能需求（FR1, FR2, FR3, FR4）
- 描述中包含精确的文件路径

## Path Conventions

- **Project Type**: CLI 工具（单项目结构）
- **Source**: `src/`
- **Tests**: `tests/`
- **Scripts**: `scripts/`

---

## Phase 1: Setup (基础设施)

**Purpose**: 项目初始化和基础结构准备

- [X] T001 确认项目依赖已安装（requests, tomllib/tomli, pytest）
- [X] T002 [P] 创建 `src/auth/token_manager.py` 空模块文件
- [X] T003 [P] 创建 `src/core/storage_manager.py` 空模块文件
- [X] T004 [P] 创建 `scripts/migrate_tracker.py` 空脚本文件
- [X] T005 [P] 创建 `tests/test_token_manager.py` 空测试文件
- [X] T006 [P] 创建 `tests/test_storage_manager.py` 空测试文件

---

## Phase 2: Foundational (数据模型扩展)

**Purpose**: 核心数据结构扩展，所有功能需求的前置条件

**⚠️ CRITICAL**: 此阶段必须完成后才能开始功能需求实现

- [X] T007 修改 `src/core/config.py` 添加 team.json 新字段解析（access_token, refresh_token, token_expires_at）
- [X] T008 修改 `src/core/config.py` 支持旧格式字段映射（token → access_token, accessToken → access_token）
- [X] T009 修改 `src/core/utils.py` 添加 invitation_status 字段支持（替代 status）
- [X] T010 修改 `src/core/utils.py` 添加 storage_status 嵌套结构支持
- [X] T011 修改 `src/core/utils.py` 实现向后兼容的 tracker 加载逻辑（自动转换旧格式）

**Checkpoint**: 数据模型扩展完成，可以开始功能需求实现

---

## Phase 3: FR-1 Token 管理增强 (Priority: P1) 🎯 MVP

**Goal**: 实现 Token 提取、刷新和更新功能，支持 refresh_token 存储和自动刷新

**Independent Test**: 运行 `pytest tests/test_token_manager.py` 验证 Token 管理功能

### Tests for FR-1

> **NOTE: 先编写测试，确保测试失败后再实现**

- [X] T012 [P] [FR1] 编写 `extract_tokens_from_response()` 单元测试 in tests/test_token_manager.py
- [X] T013 [P] [FR1] 编写 `is_token_expired()` 单元测试 in tests/test_token_manager.py
- [X] T014 [P] [FR1] 编写 `refresh_access_token()` 单元测试（含 mock）in tests/test_token_manager.py
- [X] T015 [P] [FR1] 编写 `update_team_tokens()` 单元测试 in tests/test_token_manager.py

### Implementation for FR-1

- [X] T016 [FR1] 实现 `extract_tokens_from_response()` 函数 in src/auth/token_manager.py
- [X] T017 [FR1] 实现 `is_token_expired()` 函数 in src/auth/token_manager.py
- [X] T018 [FR1] 实现 `refresh_access_token()` 函数 in src/auth/token_manager.py
- [X] T019 [FR1] 实现 `update_team_tokens()` 函数 in src/auth/token_manager.py
- [X] T020 [FR1] 添加 Token 刷新重试机制（最多 3 次）in src/auth/token_manager.py
- [X] T021 [FR1] 添加 Token 操作日志记录 in src/auth/token_manager.py

**Checkpoint**: FR-1 完成，Token 管理功能可独立测试

---

## Phase 4: FR-2 状态字段重构 (Priority: P1)

**Goal**: 将 status 字段重命名为 invitation_status，明确状态语义

**Independent Test**: 运行迁移脚本并验证 team_tracker.json 格式正确

### Implementation for FR-2

- [X] T022 [FR2] 实现迁移脚本主逻辑：备份原文件 in scripts/migrate_tracker.py
- [X] T023 [FR2] 实现迁移脚本：status → invitation_status 字段转换 in scripts/migrate_tracker.py
- [X] T024 [FR2] 实现迁移脚本：初始化 storage_status 空结构 in scripts/migrate_tracker.py
- [X] T025 [FR2] 实现迁移脚本：保存新格式并验证 in scripts/migrate_tracker.py
- [X] T026 [FR2] 添加迁移脚本命令行参数支持（--dry-run, --backup-dir）in scripts/migrate_tracker.py

**Checkpoint**: FR-2 完成，迁移脚本可独立运行

---

## Phase 5: FR-4 服务商查询接口 (Priority: P2)

**Goal**: 为 CRS/CPA/S2A 实现账号查询接口，用于检测入库状态

**Independent Test**: 运行各服务商查询接口的单元测试

### Tests for FR-4

- [X] T027 [P] [FR4] 编写 `crs_query_account()` 单元测试（含 mock）in tests/test_storage_manager.py
- [X] T028 [P] [FR4] 编写 `cpa_query_account()` 单元测试（含 mock）in tests/test_storage_manager.py
- [X] T029 [P] [FR4] 编写 `s2a_query_account()` 单元测试（含 mock）in tests/test_storage_manager.py

### Implementation for FR-4

- [X] T030 [FR4] 实现 `crs_query_account()` 函数 in src/auth/crs/client.py
- [X] T031 [FR4] 实现 `cpa_query_account()` 函数 in src/auth/cpa/client.py
- [X] T032 [FR4] 实现 `s2a_query_account()` 函数 in src/auth/s2a/client.py
- [X] T033 [FR4] 添加查询接口错误处理和重试机制 in src/auth/*/client.py

**Checkpoint**: FR-4 完成，服务商查询接口可独立测试

---

## Phase 6: FR-3 入库状态管理 (Priority: P2)

**Goal**: 实现入库状态初始化、查询和更新功能

**Independent Test**: 运行 `pytest tests/test_storage_manager.py` 验证入库状态管理功能

### Tests for FR-3

- [X] T034 [P] [FR3] 编写 `init_storage_status()` 单元测试 in tests/test_storage_manager.py
- [X] T035 [P] [FR3] 编写 `check_account_stored()` 单元测试 in tests/test_storage_manager.py
- [X] T036 [P] [FR3] 编写 `update_storage_status()` 单元测试 in tests/test_storage_manager.py
- [X] T037 [P] [FR3] 编写 `get_enabled_providers()` 单元测试 in tests/test_storage_manager.py

### Implementation for FR-3

- [X] T038 [FR3] 实现 `init_storage_status()` 函数 in src/core/storage_manager.py
- [X] T039 [FR3] 实现 `get_enabled_providers()` 函数 in src/core/storage_manager.py
- [X] T040 [FR3] 实现 `check_account_stored()` 函数（调用服务商查询接口）in src/core/storage_manager.py
- [X] T041 [FR3] 实现 `update_storage_status()` 函数 in src/core/storage_manager.py
- [X] T042 [FR3] 添加入库状态操作日志记录 in src/core/storage_manager.py

**Checkpoint**: FR-3 完成，入库状态管理功能可独立测试

---

## Phase 7: 集成与工作流

**Purpose**: 将新模块集成到现有工作流中

- [X] T043 修改 `src/core/workflow.py` 集成 Token 自动刷新检查
- [X] T044 修改 `src/core/workflow.py` 集成入库状态检测（入库前查询）
- [X] T045 修改 `src/core/workflow.py` 更新 invitation_status 状态转换逻辑
- [X] T046 编写集成测试：完整登录到入库流程 in tests/test_integration.py
- [X] T047 编写集成测试：Token 自动刷新机制 in tests/test_integration.py

**Checkpoint**: 所有功能已集成到工作流

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: 优化和完善

- [X] T048 [P] 添加文件锁机制防止并发写入冲突 in src/core/utils.py
- [X] T049 [P] 实现原子性写入（临时文件 + 重命名）in src/core/utils.py
- [X] T050 运行 quickstart.md 验证场景
- [X] T051 代码审查和清理

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖 - 可立即开始
- **Foundational (Phase 2)**: 依赖 Setup 完成 - **阻塞所有功能需求**
- **FR-1 (Phase 3)**: 依赖 Foundational 完成
- **FR-2 (Phase 4)**: 依赖 Foundational 完成（可与 FR-1 并行）
- **FR-4 (Phase 5)**: 依赖 Foundational 完成（可与 FR-1/FR-2 并行）
- **FR-3 (Phase 6)**: 依赖 Foundational + FR-4 完成
- **集成 (Phase 7)**: 依赖 FR-1, FR-2, FR-3, FR-4 完成
- **Polish (Phase 8)**: 依赖集成完成

### Functional Requirement Dependencies

```
Foundational (Phase 2)
        │
        ├──────────────────┬──────────────────┐
        ▼                  ▼                  ▼
    FR-1 (P3)          FR-2 (P4)          FR-4 (P5)
        │                  │                  │
        │                  │                  ▼
        │                  │              FR-3 (P6)
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                           ▼
                    Integration (P7)
                           │
                           ▼
                      Polish (P8)
```

### Within Each Functional Requirement

- 测试 MUST 先编写并 FAIL
- 实现后测试 MUST PASS
- 完成当前 FR 后再进入下一个

### Parallel Opportunities

- Phase 1: T002-T006 可并行
- Phase 3: T012-T015 测试可并行
- Phase 5: T027-T029 测试可并行，T030-T032 实现可并行
- Phase 6: T034-T037 测试可并行
- Phase 8: T048-T049 可并行

---

## Parallel Example: FR-1 Token Management

```bash
# 并行启动所有 FR-1 测试任务:
Task: "编写 extract_tokens_from_response() 单元测试 in tests/test_token_manager.py"
Task: "编写 is_token_expired() 单元测试 in tests/test_token_manager.py"
Task: "编写 refresh_access_token() 单元测试 in tests/test_token_manager.py"
Task: "编写 update_team_tokens() 单元测试 in tests/test_token_manager.py"
```

---

## Implementation Strategy

### MVP First (FR-1 + FR-2)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational (CRITICAL - 阻塞所有 FR)
3. 完成 Phase 3: FR-1 Token 管理
4. 完成 Phase 4: FR-2 状态字段重构
5. **STOP and VALIDATE**: 测试 Token 管理和迁移脚本
6. 可部署/演示 MVP

### Incremental Delivery

1. Setup + Foundational → 基础就绪
2. 添加 FR-1 → 测试 → 部署 (Token 管理)
3. 添加 FR-2 → 测试 → 部署 (状态重构)
4. 添加 FR-4 → 测试 → 部署 (服务商查询)
5. 添加 FR-3 → 测试 → 部署 (入库状态管理)
6. 集成 + Polish → 完整功能

### Parallel Team Strategy

多开发者场景：

1. 团队共同完成 Setup + Foundational
2. Foundational 完成后：
   - 开发者 A: FR-1 Token 管理
   - 开发者 B: FR-2 状态重构 + FR-4 服务商查询
   - 开发者 C: FR-3 入库状态管理（等待 FR-4）
3. 各 FR 独立完成后集成

---

## Notes

- [P] 任务 = 不同文件，无依赖
- [Story] 标签映射任务到具体功能需求
- 每个功能需求应可独立完成和测试
- 实现前确保测试失败
- 每个任务或逻辑组完成后提交
- 在任何检查点停止以独立验证功能
- 避免：模糊任务、同文件冲突、破坏独立性的跨 FR 依赖
