from __future__ import annotations

import argparse

from src.core.workflow import show_status


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("status", help="查看当前进度")
    parser.set_defaults(func=status_command)


def status_command(_: argparse.Namespace) -> int:
    show_status()
    return 0
