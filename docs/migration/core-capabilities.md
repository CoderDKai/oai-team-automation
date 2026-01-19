# 核心能力清单

| ID | 名称 | 入口 | 说明 | 状态 |
| --- | --- | --- | --- | --- |
| email | 邮箱服务 | `src/email/service.py` | 统一邮箱创建与验证码获取 | active |
| team | Team 服务 | `src/team/service.py` | Team 邀请、席位与账号状态 | active |
| automation | 浏览器自动化 | `src/automation/browser.py` | 注册与授权自动化流程 | active |
| auth-crs | CRS 授权 | `src/auth/crs/client.py` | CRS 授权与账号入库 | active |
| auth-cpa | CPA 授权 | `src/auth/cpa/client.py` | CPA 授权与回调处理 | active |
| auth-s2a | S2A 授权 | `src/auth/s2a/client.py` | S2A 授权与入库 | active |
| workflow | 工作流编排 | `src/core/workflow.py` | 统一编排核心流程 | active |
| cli | CLI 入口 | `run.py` | 命令行调度入口 | active |
