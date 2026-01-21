# Implementation Plan: 重构并整合 oai-team-auto-config

**Branch**: `[001-refactor-auto-config]` | **Date**: 2026-01-19 | **Spec**: `/Users/geniusk/Projects/Scripts/python/oai-team-automation/specs/001-refactor-auto-config/spec.md`
**Input**: Feature specification from `/Users/geniusk/Projects/Scripts/python/oai-team-automation/specs/001-refactor-auto-config/spec.md`

## Summary

本次实现以“将 reference/oai-team-auto-config 整合进当前项目”为目标，优先建立清晰的模块结构与入口，并提供迁移与验收路径，确保核心用例行为一致、配置变更流程可复核、旧项目使用边界可被执行。

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: DrissionPage, requests, rich, tomli
**Storage**: 本地文件（TOML/JSON/CSV）
**Testing**: pytest
**Target Platform**: 本地 CLI（macOS/Linux）+ Chrome
**Project Type**: single
**Performance Goals**: 面向批量自动化任务，强调稳定与可复现
**Constraints**: 依赖外部邮箱与授权服务；需要可用浏览器环境
**Scale/Scope**: 单次批量处理 10-100+ 账号规模

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Source: `/Users/geniusk/Projects/Scripts/python/oai-team-automation/.specify/memory/constitution.md`
- Status (Pre-Research): PASS — 仅有占位模板，暂无可执行原则或硬性约束
- Status (Post-Design): PASS — 设计方案未引入与模板占位内容冲突的规则

## Project Structure

### Documentation (this feature)

```text
specs/001-refactor-auto-config/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── cli/
├── core/
├── automation/
├── email/
├── team/
├── auth/
│   ├── crs/
│   ├── cpa/
│   └── s2a/
└── single/

main.py
config.toml.example
team.json.example

logs/

docs/
└── migration/

tests/
├── unit/
├── integration/
└── contract/

reference/
└── oai-team-auto-config/  # legacy, read-only during migration
```

**Structure Decision**: 采用单项目结构，将核心能力迁移到根目录 `src/` 与对应入口；旧项目保留在 `reference/` 作为只读参考，待迁移验收完成后再清理。
