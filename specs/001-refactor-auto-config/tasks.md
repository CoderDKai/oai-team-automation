# Tasks: 重构并整合 oai-team-auto-config

**Input**: Design documents from `/Users/geniusk/Projects/Scripts/python/oai-team-automation/specs/001-refactor-auto-config/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: 未在需求中明确要求，当前任务清单不包含测试任务。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件、无依赖）
- **[Story]**: 仅用户故事任务标记（US1/US2/US3）
- 任务描述包含明确文件路径

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 初始化项目结构与迁移文档骨架

- [X] T001 Create base package scaffolding in `src/__init__.py`, `src/cli/__init__.py`, `src/core/__init__.py`, `src/automation/__init__.py`, `src/email/__init__.py`, `src/team/__init__.py`, `src/auth/__init__.py`, `src/auth/crs/__init__.py`, `src/auth/cpa/__init__.py`, `src/auth/s2a/__init__.py`, `src/single/__init__.py`
- [X] T002 [P] Create migration docs entrypoint at `docs/migration/README.md`
- [X] T003 [P] Add configuration templates at `config.toml.example` and `team.json.example`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 全局共享基础能力（阻塞所有用户故事）

- [X] T004 Implement configuration loader and validation in `src/core/config.py`
- [X] T005 Implement logging setup in `src/core/logger.py`
- [X] T006 Implement shared file/status utilities in `src/core/utils.py`
- [X] T007 Define domain models in `src/core/models.py`
- [X] T008 Implement migration record store in `src/core/migration_store.py`
- [X] T009 Implement CLI framework skeleton in `src/cli/main.py` and `src/cli/commands/__init__.py`
- [X] T010 Wire CLI entrypoint in `main.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 统一整合配置能力 (Priority: P1) 🎯 MVP

**Goal**: 将核心能力迁移到新结构并提供清晰入口

**Independent Test**: 维护者可在新结构中定位所有核心能力入口，并完成等价用例执行

### Implementation for User Story 1

- [X] T011 [P] [US1] Create capability catalog in `docs/migration/core-capabilities.md`
- [X] T012 [P] [US1] Port email service to `src/email/service.py`
- [X] T013 [P] [US1] Port team service to `src/team/service.py`
- [X] T014 [P] [US1] Port browser automation to `src/automation/browser.py`
- [X] T015 [P] [US1] Port auth services to `src/auth/crs/client.py`, `src/auth/cpa/client.py`, `src/auth/s2a/client.py`
- [X] T016 [US1] Implement workflow orchestration in `src/core/workflow.py`
- [X] T017 [US1] Implement CLI commands in `src/cli/commands/start.py` and `src/cli/commands/status.py`
- [X] T018 [US1] Update entrypoints and module map in `docs/migration/README.md`

**Checkpoint**: User Story 1 should be fully functional and independently verifiable

---

## Phase 4: User Story 2 - 规范化变更流程 (Priority: P2)

**Goal**: 形成统一的配置变更规范与复核流程

**Independent Test**: 贡献者可按文档完成一次配置变更并被维护者复核通过

### Implementation for User Story 2

- [X] T019 [P] [US2] Create change guidelines in `docs/migration/change-guidelines.md`
- [X] T020 [P] [US2] Create change request template in `docs/migration/change-template.md`
- [X] T021 [P] [US2] Create module catalog in `docs/migration/module-catalog.md`
- [X] T022 [US2] Implement config validation command in `src/cli/commands/validate.py`
- [X] T023 [US2] Document collaboration workflow in `docs/migration/collaboration-workflow.md`

**Checkpoint**: User Story 2 should be independently usable for config change workflows

---

## Phase 5: User Story 3 - 平滑迁移既有使用者 (Priority: P3)

**Goal**: 提供迁移路径与验收记录，确保旧配置可平滑迁移

**Independent Test**: 典型配置可迁移并生成可复核的迁移记录

### Implementation for User Story 3

- [X] T024 [P] [US3] Create legacy mapping doc in `docs/migration/legacy-map.md`
- [X] T025 [US3] Implement migration mapping and transform in `src/core/migration.py`
- [X] T026 [US3] Implement migration CLI in `src/cli/commands/migrate.py`
- [X] T027 [US3] Add migration report template in `docs/migration/migration-report-template.md`

**Checkpoint**: User Story 3 should be independently runnable for migration verification

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 跨故事完善与收尾

- [X] T028 [P] Update root usage documentation in `README.md`
- [X] T029 [P] Validate quickstart steps and update `specs/001-refactor-auto-config/quickstart.md`
- [X] T030 [P] Add migration checklist in `docs/migration/migration-checklist.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖
- **Foundational (Phase 2)**: 依赖 Setup 完成，阻塞所有用户故事
- **User Stories (Phase 3+)**: 依赖 Foundational 完成
- **Polish (Phase 6)**: 依赖所需用户故事完成

### User Story Dependencies

- **US1 (P1)**: 仅依赖 Foundational
- **US2 (P2)**: 依赖 Foundational，可与 US1 并行但建议在 US1 结构稳定后进行
- **US3 (P3)**: 依赖 Foundational，且依赖 US1 的核心能力入口已确定

### Parallel Opportunities (Per Story)

- **US1**: T011, T012, T013, T014, T015 可并行；T016 与 T017 依赖前述模块完成
- **US2**: T019, T020, T021 可并行；T022 与 T023 可并行
- **US3**: T024 可并行；T025 后再执行 T026/T027

---

## Parallel Example: User Story 1

```bash
Task: "Create capability catalog in docs/migration/core-capabilities.md"
Task: "Port email service to src/email/service.py"
Task: "Port team service to src/team/service.py"
Task: "Port browser automation to src/automation/browser.py"
Task: "Port auth services to src/auth/crs/client.py, src/auth/cpa/client.py, src/auth/s2a/client.py"
```

## Parallel Example: User Story 2

```bash
Task: "Create change guidelines in docs/migration/change-guidelines.md"
Task: "Create change request template in docs/migration/change-template.md"
Task: "Create module catalog in docs/migration/module-catalog.md"
```

## Parallel Example: User Story 3

```bash
Task: "Create legacy mapping doc in docs/migration/legacy-map.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational
3. 完成 Phase 3: User Story 1
4. 独立验证 US1 入口与核心用例一致性

### Incremental Delivery

1. Setup + Foundational → 基础就绪
2. US1 → 验证核心能力整合
3. US2 → 验证配置变更流程
4. US3 → 验证迁移路径与验收记录
5. Polish → 文档与收尾
