# Quickstart: 重构并整合 oai-team-auto-config

**Date**: 2026-01-19
**Feature Spec**: /Users/geniusk/Projects/Scripts/python/oai-team-automation/specs/001-refactor-auto-config/spec.md

## 目标

在当前项目中完成核心能力整合、配置规范化与迁移验收，确保使用者无需回退到旧项目。

## 前置条件

- 可用的 Python 3.12 环境
- 可用的浏览器环境（如 Chrome）
- 可访问的邮箱与授权服务配置

## 快速流程

1. 准备配置模板并填充必要信息（如账号、服务端点与授权信息）
2. 通过 `python main.py validate` 校验配置
3. 确认核心能力清单与对应的新结构入口
4. 执行迁移流程，将典型配置从旧项目映射到新结构
5. 运行核心用例验证迁移一致性（`python main.py start`）
6. 记录迁移结果与差异说明，形成验收结论

## 验证与回退

- 通过迁移记录确认所有核心能力已完成验证
- 若发现差异，记录原因并修正映射或配置后重试
- 在验收完成前，旧项目保持只读以便对照
