#!/usr/bin/env python3
# ==================== 数据迁移脚本 ====================
# 将 team_tracker.json 从旧格式迁移到新格式

"""Migrate Tracker - 迁移 team_tracker.json 数据格式

功能:
    - 备份原文件
    - status → invitation_status 字段转换
    - 初始化 storage_status 空结构
    - 保存新格式并验证

用法:
    python scripts/migrate_tracker.py [--dry-run] [--backup-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from src.core.config import TEAM_TRACKER_FILE


PROVIDERS = ("crs", "cpa", "s2a")


def _init_storage_status() -> dict:
    return {provider: {"status": "not_stored"} for provider in PROVIDERS}


def _normalize_storage_status(value: object) -> tuple[dict, bool]:
    if not isinstance(value, dict):
        return _init_storage_status(), True

    changed = False
    normalized = deepcopy(value)
    for provider in PROVIDERS:
        entry = normalized.get(provider)
        if not isinstance(entry, dict):
            normalized[provider] = {"status": "not_stored"}
            changed = True
            continue
        if not entry.get("status"):
            entry["status"] = "not_stored"
            changed = True
    return normalized, changed


def _migrate_account(account: dict) -> tuple[dict, bool, dict]:
    updated = deepcopy(account)
    report = {
        "status_migrated": 0,
        "status_initialized": 0,
        "storage_added": 0,
        "storage_fixed": 0,
    }

    if "status" in updated and "invitation_status" not in updated:
        updated["invitation_status"] = updated.pop("status")
        report["status_migrated"] += 1
    elif "status" in updated and "invitation_status" in updated:
        updated.pop("status")
        report["status_migrated"] += 1

    if "invitation_status" not in updated:
        updated["invitation_status"] = ""
        report["status_initialized"] += 1

    if "storage_status" not in updated:
        updated["storage_status"] = _init_storage_status()
        report["storage_added"] += 1
    else:
        normalized, changed = _normalize_storage_status(updated["storage_status"])
        if changed:
            updated["storage_status"] = normalized
            report["storage_fixed"] += 1

    return updated, updated != account, report


def _migrate_tracker(tracker: dict) -> tuple[dict, dict, dict]:
    updated_tracker = deepcopy(tracker)
    totals = {
        "teams": 0,
        "accounts": 0,
        "status_migrated": 0,
        "status_initialized": 0,
        "storage_added": 0,
        "storage_fixed": 0,
    }
    per_team_changes: dict[str, int] = {}

    teams = updated_tracker.get("teams")
    if not isinstance(teams, dict):
        updated_tracker["teams"] = {}
        return updated_tracker, totals, per_team_changes

    totals["teams"] = len(teams)
    for team_name, accounts in teams.items():
        if not isinstance(accounts, list):
            teams[team_name] = []
            per_team_changes[team_name] = 0
            continue
        migrated_accounts = []
        team_changed = 0
        for account in accounts:
            if not isinstance(account, dict):
                continue
            totals["accounts"] += 1
            migrated, changed, report = _migrate_account(account)
            migrated_accounts.append(migrated)
            if changed:
                team_changed += 1
            for key in (
                "status_migrated",
                "status_initialized",
                "storage_added",
                "storage_fixed",
            ):
                totals[key] += report[key]
        teams[team_name] = migrated_accounts
        if team_changed:
            per_team_changes[team_name] = team_changed

    return updated_tracker, totals, per_team_changes


def _validate_tracker(tracker: dict) -> list[str]:
    errors: list[str] = []
    teams = tracker.get("teams")
    if not isinstance(teams, dict):
        errors.append("teams 字段不是字典")
        return errors

    for team_name, accounts in teams.items():
        if not isinstance(accounts, list):
            errors.append(f"团队 {team_name} 的账号列表不是列表")
            continue
        for account in accounts:
            if not isinstance(account, dict):
                errors.append(f"团队 {team_name} 存在非字典账号记录")
                continue
            if "status" in account:
                errors.append(f"团队 {team_name} 仍包含 status 字段")
            if "invitation_status" not in account:
                errors.append(f"团队 {team_name} 缺少 invitation_status 字段")
            storage_status = account.get("storage_status")
            if not isinstance(storage_status, dict):
                errors.append(f"团队 {team_name} storage_status 非字典")
                continue
            for provider in PROVIDERS:
                entry = storage_status.get(provider)
                if not isinstance(entry, dict):
                    errors.append(f"团队 {team_name} storage_status 缺少 {provider}")
                    continue
                if not entry.get("status"):
                    errors.append(
                        f"团队 {team_name} storage_status.{provider}.status 为空"
                    )

    return errors


def _create_backup(tracker_path: Path, backup_dir: Path | None) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    destination_dir = backup_dir or tracker_path.parent
    destination_dir.mkdir(parents=True, exist_ok=True)
    backup_name = f"{tracker_path.stem}.bak-{timestamp}{tracker_path.suffix}"
    backup_path = destination_dir / backup_name
    shutil.copy2(tracker_path, backup_path)
    return backup_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="迁移 team_tracker.json 到新格式")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只显示变更，不实际修改文件",
    )
    parser.add_argument(
        "--backup-dir",
        metavar="DIR",
        help="指定备份目录（默认与原文件同目录）",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    tracker_path = Path(TEAM_TRACKER_FILE)
    if not tracker_path.exists():
        print(f"未找到追踪文件: {tracker_path}")
        return 1

    with tracker_path.open("r", encoding="utf-8") as f:
        tracker = json.load(f)

    migrated, totals, per_team_changes = _migrate_tracker(tracker)
    errors = _validate_tracker(migrated)
    if errors:
        print("迁移结果验证失败:")
        for error in errors:
            print(f"- {error}")
        return 1

    has_changes = migrated != tracker
    print(f"读取文件: {tracker_path}")
    print(f"团队数量: {totals['teams']} | 账号数量: {totals['accounts']}")
    print(
        "字段变更统计: "
        f"status 迁移 {totals['status_migrated']}，"
        f"invitation_status 初始化 {totals['status_initialized']}，"
        f"storage_status 新增 {totals['storage_added']}，"
        f"storage_status 修复 {totals['storage_fixed']}"
    )
    if per_team_changes:
        print("团队变更:")
        for team_name, changed in sorted(per_team_changes.items()):
            print(f"- {team_name}: {changed} 条记录")

    if args.dry_run:
        print("已启用 --dry-run，未执行写入。")
        return 0

    if not has_changes:
        print("无需迁移，文件已是最新格式。")
        return 0

    backup_dir = Path(args.backup_dir) if args.backup_dir else None
    backup_path = _create_backup(tracker_path, backup_dir)
    print(f"已备份: {backup_path}")

    with tracker_path.open("w", encoding="utf-8") as f:
        json.dump(migrated, f, ensure_ascii=False, indent=2)

    with tracker_path.open("r", encoding="utf-8") as f:
        saved = json.load(f)

    saved_errors = _validate_tracker(saved)
    if saved_errors:
        print("保存后验证失败:")
        for error in saved_errors:
            print(f"- {error}")
        return 1

    print("迁移完成并验证通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
