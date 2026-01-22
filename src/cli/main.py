import argparse
import sys

from src.cli.commands import migrate as migrate_cmd
from src.cli.commands import register as register_cmd
from src.cli.commands import start as start_cmd
from src.cli.commands import status as status_cmd
from src.cli.commands import validate as validate_cmd


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="oai-team-auto-config")
    subparsers = parser.add_subparsers(dest="command")

    start_cmd.add_parser(subparsers)
    status_cmd.add_parser(subparsers)
    validate_cmd.add_parser(subparsers)
    migrate_cmd.add_parser(subparsers)
    register_cmd.add_parser(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
