# Migration Guide: oai-team-auto-config

本目录用于记录从 legacy 项目到当前仓库结构的迁移说明、模块映射与流程规范。

## 目录结构

- `core-capabilities.md`: 核心能力清单与入口
- `module-catalog.md`: 模块目录与负责人
- `change-guidelines.md`: 配置变更规范
- `change-template.md`: 配置变更申请模板
- `collaboration-workflow.md`: 协作与复核流程
- `legacy-map.md`: 旧结构到新结构的映射
- `migration-report-template.md`: 迁移验收报告模板
- `migration-checklist.md`: 迁移清单

## 新结构模块入口

- `src/core/`: 配置、日志、模型、迁移与流程编排
- `src/cli/`: CLI 入口与子命令
- `src/email/`: 邮箱服务
- `src/team/`: Team 邀请与状态
- `src/automation/`: 浏览器自动化
- `src/auth/`: CRS/CPA/S2A 授权客户端
- `src/single/`: 单人/批量脚本入口 (逐步迁移)
- `main.py`: CLI 入口脚本

## 模块映射

| 旧模块 | 新入口 | 说明 |
| --- | --- | --- |
| `reference/oai-team-auto-config/src/email/email_service.py` | `src/email/service.py` | 邮箱创建与验证码 |
| `reference/oai-team-auto-config/src/team/team_service.py` | `src/team/service.py` | Team 邀请与状态 |
| `reference/oai-team-auto-config/src/automation/browser_automation.py` | `src/automation/browser.py` | 浏览器自动化 |
| `reference/oai-team-auto-config/src/crs/crs_service.py` | `src/auth/crs/client.py` | CRS 授权 |
| `reference/oai-team-auto-config/src/cpa/cpa_service.py` | `src/auth/cpa/client.py` | CPA 授权 |
| `reference/oai-team-auto-config/src/s2a/s2a_service.py` | `src/auth/s2a/client.py` | S2A 授权 |
| `reference/oai-team-auto-config/run.py` | `main.py` | CLI 入口与工作流编排入口 |

## 使用建议

1. 先确认 `core-capabilities.md` 的入口与用途
2. 按需阅读变更规范与协作流程
3. 迁移时对照 `legacy-map.md` 与验收模板记录差异
