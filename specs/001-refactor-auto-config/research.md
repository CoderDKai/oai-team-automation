# Research: 重构并整合 oai-team-auto-config

**Date**: 2026-01-19
**Feature Spec**: /Users/geniusk/Projects/Scripts/python/oai-team-automation/specs/001-refactor-auto-config/spec.md

## Findings

### Decision 1: 以 Python 3.12 作为运行时基线
- **Decision**: 采用 Python 3.12 作为本项目的基础运行环境
- **Rationale**: 参考项目已声明 Python 3.12+，保持一致可降低迁移风险
- **Alternatives considered**: 维持兼容 3.10/3.11（会增加适配成本）

### Decision 2: 以文件存储为主要状态载体
- **Decision**: 配置与状态记录继续使用 TOML/JSON/CSV 等文件
- **Rationale**: 现有流程已依赖文件格式，迁移成本最低且满足现有需求
- **Alternatives considered**: 引入数据库（增加运维与迁移复杂度）

### Decision 3: 单项目结构 + legacy 冻结
- **Decision**: 迁移后的结构统一落在仓库根目录，并保留 legacy 只读目录
- **Rationale**: 便于协作与维护，同时保留对比与回溯路径
- **Alternatives considered**: 保留独立子项目（会维持分裂的入口与规范）

### Decision 4: 以 pytest 建立测试基线
- **Decision**: 统一使用 pytest 作为自动化测试入口
- **Rationale**: 参考项目已有 pytest 使用痕迹，生态完善
- **Alternatives considered**: 维持脚本式测试（难以形成稳定回归）

### Decision 5: 以 CLI 批处理作为主要交互形式
- **Decision**: 保持以 CLI 批处理为核心入口
- **Rationale**: 现有工作流以批量自动化为主，CLI 便于集成与操作
- **Alternatives considered**: 引入 Web UI（与当前需求不匹配）
