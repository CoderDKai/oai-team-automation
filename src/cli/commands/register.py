from __future__ import annotations

import argparse


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("register", help="根据账号列表注册新用户")
    parser.add_argument(
        "--file",
        default="accounts.json",
        help="账号 JSON 文件路径或 JSON 字符串 (默认: accounts.json)",
    )
    parser.set_defaults(func=register_command)


def register_command(args: argparse.Namespace) -> int:
    from src.single.register import register_from_source

    return register_from_source(args.file)
