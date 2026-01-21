# Data Model: 重构并整合 oai-team-auto-config

**Date**: 2026-01-19
**Feature Spec**: /Users/geniusk/Projects/Scripts/python/oai-team-automation/specs/001-refactor-auto-config/spec.md

## Entities

### 配置模块 (ConfigModule)

**Purpose**: 按用途归类配置集合，作为可定位入口与说明载体。

**Fields**:
- id: 模块唯一标识
- name: 模块名称
- purpose: 模块用途说明
- owner: 负责人/维护者
- entrypoint: 入口说明或位置标识
- status: active | deprecated | legacy
- updated_at: 最近更新日期

**Relationships**:
- 1 个配置模块包含多个配置项

**Validation Rules**:
- name 必填且全局唯一
- entrypoint 必填且可定位
- status 只能取上述枚举值

---

### 配置项 (ConfigItem)

**Purpose**: 描述可调整配置的最小单位，支持变更与复核。

**Fields**:
- id: 配置项唯一标识
- module_id: 所属配置模块 id
- name: 配置项名称
- description: 用途说明
- scope: 适用范围
- constraints: 使用约束或校验规则
- default_value: 默认值（如适用）
- source: legacy | refactored
- status: active | deprecated

**Relationships**:
- 多个配置项隶属于一个配置模块

**Validation Rules**:
- module_id 必须存在
- name 在同一模块内唯一
- scope 必填

---

### 迁移记录 (MigrationRecord)

**Purpose**: 追踪旧项目能力或配置到新项目的迁移过程与验证结果。

**Fields**:
- id: 迁移记录唯一标识
- legacy_path: 旧项目对应位置或标识
- new_path: 新项目对应位置或标识
- capability_id: 对应核心能力 id（如适用）
- status: pending | migrated | verified | failed
- verified_by: 验证人
- verified_at: 验证时间
- notes: 备注与差异说明

**Relationships**:
- 可关联多个配置项或模块

**Validation Rules**:
- legacy_path 与 new_path 必填
- status 只允许合法状态流转

**State Transitions**:
- pending -> migrated -> verified
- pending -> failed
- migrated -> failed (回退或验证失败)
