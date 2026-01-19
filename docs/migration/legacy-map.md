# 旧结构映射

| 旧路径 | 新路径 | 说明 |
| --- | --- | --- |
| `reference/oai-team-auto-config/run.py` | `src/core/workflow.py` + `run.py` | 工作流与 CLI 入口拆分 |
| `reference/oai-team-auto-config/src/core/config.py` | `src/core/config.py` | 配置加载 |
| `reference/oai-team-auto-config/src/core/logger.py` | `src/core/logger.py` | 日志输出 |
| `reference/oai-team-auto-config/src/core/utils.py` | `src/core/utils.py` | 通用工具 |
| `reference/oai-team-auto-config/src/email/email_service.py` | `src/email/service.py` | 邮箱服务 |
| `reference/oai-team-auto-config/src/team/team_service.py` | `src/team/service.py` | Team 服务 |
| `reference/oai-team-auto-config/src/automation/browser_automation.py` | `src/automation/browser.py` | 浏览器自动化 |
| `reference/oai-team-auto-config/src/crs/crs_service.py` | `src/auth/crs/client.py` | CRS 授权 |
| `reference/oai-team-auto-config/src/cpa/cpa_service.py` | `src/auth/cpa/client.py` | CPA 授权 |
| `reference/oai-team-auto-config/src/s2a/s2a_service.py` | `src/auth/s2a/client.py` | S2A 授权 |
