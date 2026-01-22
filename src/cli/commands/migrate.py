from __future__ import annotations

import argparse

from src.core.logger import log


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("migrate", help="管理迁移记录")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list", action="store_true", help="列出迁移记录")
    group.add_argument("--create", action="store_true", help="创建迁移记录")
    group.add_argument("--verify", action="store_true", help="验收迁移记录")

    parser.add_argument("--id", dest="record_id", help="迁移记录 ID")
    parser.add_argument("--legacy", dest="legacy_path", help="旧路径")
    parser.add_argument("--new", dest="new_path", help="新路径")
    parser.add_argument("--capability-id", help="能力 ID")
    parser.add_argument("--verified-by", help="验收人")
    parser.add_argument("--notes", help="备注")
    parser.set_defaults(func=migrate_command)


def migrate_command(args: argparse.Namespace) -> int:
    from src.core.migration_store import MigrationStore

    store = MigrationStore()

    if args.list:
        records = store.list_records()
        if not records:
            log.info("暂无迁移记录")
            return 0
        for record in records:
            log.info(
                f"{record.id}: {record.legacy_path} -> {record.new_path} ({record.status})"
            )
        return 0

    if args.create:
        if not args.record_id or not args.legacy_path or not args.new_path:
            log.error("创建记录需要 --id --legacy --new")
            return 1
        store.create_record(
            record_id=args.record_id,
            legacy_path=args.legacy_path,
            new_path=args.new_path,
            capability_id=args.capability_id or "",
            notes=args.notes or "",
        )
        log.success(f"已创建迁移记录: {args.record_id}")
        return 0

    if args.verify:
        if not args.record_id or not args.verified_by:
            log.error("验收记录需要 --id --verified-by")
            return 1
        try:
            store.verify(args.record_id, args.verified_by, args.notes or "")
        except KeyError as exc:
            log.error(str(exc))
            return 1
        log.success(f"已验收迁移记录: {args.record_id}")
        return 0

    log.error("请指定 --list/--create/--verify")
    return 1
