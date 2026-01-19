from __future__ import annotations

import argparse

from src.core import workflow


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("run", help="运行主流程")
    parser.add_argument("--team-index", type=int, help="仅处理指定 Team 索引")
    parser.add_argument("--test-email-only", action="store_true", help="仅测试邮箱")
    parser.set_defaults(func=run_command)


def run_command(args: argparse.Namespace) -> int:
    if args.test_email_only:
        workflow.main("test")
        return 0

    if args.team_index is not None:
        workflow.main("single", args.team_index)
        return 0

    workflow.main()
    return 0
