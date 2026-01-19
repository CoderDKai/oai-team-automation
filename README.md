# oai-team-automation

用于整合与迁移 oai-team-auto-config 的自动化工具集，提供统一的 CLI 入口与核心能力模块。

## 快速开始

1. 复制配置模板并填写必要参数:

```bash
cp config.toml.example config.toml
cp team.json.example team.json
```

2. 安装依赖后运行 CLI:

```bash
python run.py --help
```

3. 执行主流程:

```bash
python run.py run
```

## 常用命令

- `python run.py run`: 执行主流程
- `python run.py run --team-index 0`: 仅处理指定 Team
- `python run.py status`: 查看当前进度
- `python run.py validate`: 校验配置
- `python run.py migrate --list`: 查看迁移记录

## 目录结构

- `src/`: 核心实现
- `docs/migration/`: 迁移文档与模板
- `reference/`: legacy 参考实现 (只读)
