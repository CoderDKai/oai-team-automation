from __future__ import annotations

import argparse


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "create-parent-account",
        help="创建 Team 父账号并订阅 ChatGPT Team",
    )
    parser.add_argument(
        "--file",
        default="parent_accounts.json",
        help="账号 JSON 文件路径或 JSON 字符串 (默认: parent_accounts.json)",
    )
    parser.set_defaults(func=create_parent_account_command)


def create_parent_account_command(args: argparse.Namespace) -> int:
    from src.single.create_parent_account import create_parent_accounts_from_source

    return create_parent_accounts_from_source(args.file)
