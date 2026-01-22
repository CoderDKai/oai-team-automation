from __future__ import annotations

import argparse

from src.core.logger import log


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("validate", help="校验配置文件")
    parser.set_defaults(func=validate_command)


def validate_command(_: argparse.Namespace) -> int:
    from src.core.config import CONFIG_FILE, TEAM_JSON_FILE, get_config_errors

    exit_code = 0

    if not CONFIG_FILE.exists():
        log.error(f"未找到配置文件: {CONFIG_FILE}")
        exit_code = 1
    else:
        log.success(f"已找到配置文件: {CONFIG_FILE}")

    if not TEAM_JSON_FILE.exists():
        log.warning(f"未找到 Team 配置: {TEAM_JSON_FILE}")
    else:
        log.success(f"已找到 Team 配置: {TEAM_JSON_FILE}")

    errors = get_config_errors()
    if errors:
        log.error("配置加载存在问题:")
        for err in errors:
            log.error(
                f"{err.get('source')}: {err.get('message')}"
                + (f" ({err.get('details')})" if err.get("details") else "")
            )
        exit_code = 1
    else:
        log.success("配置加载无阻塞错误")

    return exit_code
