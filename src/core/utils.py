# ==================== 工具函数模块 ====================
# 通用工具函数: CSV 记录、JSON 追踪等

import os
import csv
import json
import time
import tempfile
from datetime import datetime

from src.core.config import CSV_FILE, TEAM_TRACKER_FILE
from src.core.logger import log

try:
    from filelock import FileLock, Timeout
except Exception:  # pragma: no cover - 兼容无 filelock 环境
    FileLock = None
    Timeout = None


def save_to_csv(
    email: str,
    password: str,
    team_name: str = "",
    status: str = "success",
    crs_id: str = "",
):
    """保存账号信息到 CSV 文件

    Args:
        email: 邮箱地址
        password: 密码
        team_name: Team 名称
        status: 状态 (success/failed)
        crs_id: CRS 账号 ID
    """
    file_exists = os.path.exists(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(
                ["email", "password", "team", "status", "crs_id", "timestamp"]
            )

        writer.writerow(
            [
                email,
                password,
                team_name,
                status,
                crs_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )

    log.info(f"保存到 {CSV_FILE}", icon="save")


def _migrate_account_record(account: dict) -> dict:
    """迁移单个账号记录到新格式 (向后兼容)

    字段映射:
        status → invitation_status
        (新增) storage_status
    """
    # 如果已经是新格式，直接返回
    if "invitation_status" in account:
        # 确保 storage_status 存在
        if "storage_status" not in account:
            account["storage_status"] = _init_storage_status()
        return account

    # 迁移 status → invitation_status
    if "status" in account:
        account["invitation_status"] = account.pop("status")

    # 初始化 storage_status
    if "storage_status" not in account:
        account["storage_status"] = _init_storage_status()

    return account


def _init_storage_status() -> dict:
    """初始化入库状态结构"""
    return {
        "crs": {"status": "not_stored"},
        "cpa": {"status": "not_stored"},
        "s2a": {"status": "not_stored"},
    }


def load_team_tracker() -> dict:
    """加载 Team 追踪记录 (支持新旧格式自动转换)

    Returns:
        dict: {"teams": {"team_name": [{"email": "...", "invitation_status": "...", "storage_status": {...}}]}}
    """
    if os.path.exists(TEAM_TRACKER_FILE):
        try:
            with open(TEAM_TRACKER_FILE, "r", encoding="utf-8") as f:
                tracker = json.load(f)

            # 自动迁移旧格式数据
            for team_name in tracker.get("teams", {}):
                tracker["teams"][team_name] = [
                    _migrate_account_record(acc)
                    for acc in tracker["teams"][team_name]
                ]

            return tracker
        except Exception as e:
            log.warning(f"加载追踪记录失败: {e}")

    return {"teams": {}, "last_updated": None}


def save_team_tracker(tracker: dict):
    """保存 Team 追踪记录"""
    tracker["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lock_path = f"{TEAM_TRACKER_FILE}.lock"
    if FileLock:
        try:
            with FileLock(lock_path, timeout=10):
                _atomic_write_tracker(TEAM_TRACKER_FILE, tracker)
        except Timeout:
            log.warning("保存追踪记录失败: 获取文件锁超时")
        except Exception as e:
            log.warning(f"保存追踪记录失败: {e}")
        return

    try:
        _save_tracker_with_fcntl_lock(lock_path, TEAM_TRACKER_FILE, tracker)
    except Exception as e:
        log.warning(f"保存追踪记录失败: {e}")


def _atomic_write_tracker(file_path: str, tracker: dict):
    """原子写入 tracker 数据"""
    target_dir = os.path.dirname(file_path) or "."
    base_name = os.path.basename(file_path)
    fd, temp_path = tempfile.mkstemp(prefix=f".{base_name}.", dir=target_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
            json.dump(tracker, temp_file, ensure_ascii=False, indent=2)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, file_path)
    except Exception:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as cleanup_error:
            log.warning(f"清理临时文件失败: {cleanup_error}")
        raise


def _save_tracker_with_fcntl_lock(
    lock_path: str, file_path: str, tracker: dict
):
    """使用 fcntl 锁保存 tracker (filelock 不可用时使用)"""
    import fcntl

    with open(lock_path, "w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            _atomic_write_tracker(file_path, tracker)
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def add_account_to_tracker(
    tracker: dict, team_name: str, email: str, status: str = "invited"
):
    """添加账号到追踪记录

    Args:
        tracker: 追踪记录
        team_name: Team 名称
        email: 邮箱地址
        status: 邀请状态 (invited/registered/authorized/completed)
    """
    if team_name not in tracker["teams"]:
        tracker["teams"][team_name] = []

    # 检查是否已存在
    for account in tracker["teams"][team_name]:
        if account["email"] == email:
            account["invitation_status"] = status
            account["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return

    # 添加新记录 (使用新格式)
    tracker["teams"][team_name].append(
        {
            "email": email,
            "invitation_status": status,
            "storage_status": _init_storage_status(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


def update_account_status(tracker: dict, team_name: str, email: str, status: str):
    """更新账号邀请状态"""
    if team_name in tracker["teams"]:
        for account in tracker["teams"][team_name]:
            if account["email"] == email:
                account["invitation_status"] = status
                account["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return


def remove_account_from_tracker(tracker: dict, team_name: str, email: str) -> bool:
    """从 tracker 中移除账号

    Args:
        tracker: 追踪记录
        team_name: Team 名称
        email: 邮箱地址

    Returns:
        bool: 是否成功移除
    """
    if team_name in tracker["teams"]:
        original_len = len(tracker["teams"][team_name])
        tracker["teams"][team_name] = [
            acc for acc in tracker["teams"][team_name] if acc["email"] != email
        ]
        return len(tracker["teams"][team_name]) < original_len
    return False


def get_team_account_count(tracker: dict, team_name: str) -> int:
    """获取 Team 已记录的账号数量"""
    if team_name in tracker["teams"]:
        return len(tracker["teams"][team_name])
    return 0


def get_incomplete_accounts(tracker: dict, team_name: str) -> list:
    """获取未完成的账号列表 (非 completed 状态)

    Args:
        tracker: 追踪记录
        team_name: Team 名称

    Returns:
        list: [{"email": "...", "invitation_status": "...", "password": "...", "role": "..."}]
    """
    incomplete = []
    if team_name in tracker.get("teams", {}):
        for account in tracker["teams"][team_name]:
            # 支持新旧字段名
            status = account.get("invitation_status") or account.get("status", "")
            # 只要不是 completed 都算未完成，需要继续处理
            if status != "completed":
                incomplete.append(
                    {
                        "email": account["email"],
                        "invitation_status": status,
                        "password": account.get("password", ""),
                        "role": account.get("role", "member"),
                    }
                )
    return incomplete


def get_all_incomplete_accounts(tracker: dict) -> dict:
    """获取所有 Team 的未完成账号

    Returns:
        dict: {"team_name": [{"email": "...", "status": "..."}]}
    """
    result = {}
    for team_name in tracker.get("teams", {}):
        incomplete = get_incomplete_accounts(tracker, team_name)
        if incomplete:
            result[team_name] = incomplete
    return result


def add_account_with_password(
    tracker: dict, team_name: str, email: str, password: str, status: str = "invited"
):
    """添加账号到追踪记录 (带密码)"""
    if team_name not in tracker["teams"]:
        tracker["teams"][team_name] = []

    # 检查是否已存在
    for account in tracker["teams"][team_name]:
        if account["email"] == email:
            account["status"] = status
            account["password"] = password
            account["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return

    # 添加新记录
    tracker["teams"][team_name].append(
        {
            "email": email,
            "password": password,
            "status": status,
            "role": "member",  # 角色: owner 或 member
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


def print_summary(results: list):
    """打印执行摘要

    Args:
        results: [{"team": "...", "email": "...", "status": "...", "crs_id": "..."}]
    """
    log.separator("=", 60)
    log.header("执行摘要")
    log.separator("=", 60)

    success_count = sum(1 for r in results if r.get("status") == "success")
    failed_count = len(results) - success_count

    log.info(f"总计: {len(results)} 个账号")
    log.success(f"成功: {success_count}")
    log.error(f"失败: {failed_count}")

    # 按 Team 分组
    teams = {}
    for r in results:
        team = r.get("team", "Unknown")
        if team not in teams:
            teams[team] = {"success": 0, "failed": 0, "accounts": []}

        if r.get("status") == "success":
            teams[team]["success"] += 1
        else:
            teams[team]["failed"] += 1

        teams[team]["accounts"].append(r)

    log.info("按 Team 统计:")
    for team_name, data in teams.items():
        log.info(
            f"{team_name}: 成功 {data['success']}, 失败 {data['failed']}", icon="team"
        )
        for acc in data["accounts"]:
            if acc.get("status") == "success":
                log.success(f"{acc.get('email', 'Unknown')}")
            else:
                log.error(f"{acc.get('email', 'Unknown')}")

    log.separator("=", 60)


def format_duration(seconds: float) -> str:
    """格式化时长"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


class Timer:
    """计时器"""

    def __init__(self, name: str = ""):
        self.name = name
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.time()
        if self.name:
            log.info(f"{self.name} 开始", icon="time")

    def stop(self):
        if self.start_time is None:
            return 0.0
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        if self.name:
            log.info(f"{self.name} 完成 ({format_duration(duration)})", icon="time")
        return duration

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


def add_team_owners_to_tracker(tracker: dict, password: str) -> int:
    """将 team.json 中的 Team Owner 添加到 tracker，走授权流程

    只添加有 token 的 Team Owner，没有 token 的跳过（格式3会在登录时单独处理）

    Args:
        tracker: team_tracker 数据
        password: 默认账号密码 (旧格式使用)

    Returns:
        int: 添加的数量
    """
    from src.core.config import INCLUDE_TEAM_OWNERS, get_teams

    if not INCLUDE_TEAM_OWNERS:
        return 0

    teams = get_teams()
    if not teams:
        return 0

    added_count = 0
    for team in teams:
        # 跳过没有 token 的 Team（格式3会在登录时单独处理）
        if not team.get("auth_token"):
            continue

        team_name = team.get("name", "")
        team_format = team.get("format", "old")

        # 获取邮箱
        email = team.get("owner_email", "")
        if not email:
            raw_data = team.get("raw", {})
            email = raw_data.get("user", {}).get("email", "")

        # 获取密码
        owner_password = team.get("owner_password", "") or password

        if not team_name or not email:
            continue

        # 检查是否已在 tracker 中
        existing = False
        if team_name in tracker.get("teams", {}):
            for acc in tracker["teams"][team_name]:
                if acc.get("email") == email:
                    existing = True
                    break

        if not existing:
            # 添加到 tracker
            if team_name not in tracker["teams"]:
                tracker["teams"][team_name] = []

            # 根据格式和授权状态决定 tracker 状态
            # - 新格式且已授权: 状态为 completed (跳过)
            # - 新格式未授权: 状态为 registered (需要授权)
            # - 旧格式: 使用 OTP 登录授权，状态为 team_owner
            if team_format == "new":
                if team.get("authorized"):
                    status = "completed"  # 已授权，跳过
                else:
                    status = "registered"  # 需要授权
            else:
                status = "team_owner"  # 旧格式，使用 OTP 登录授权

            tracker["teams"][team_name].append(
                {
                    "email": email,
                    "password": owner_password,
                    "status": status,
                    "role": "owner",
                    "storage_status": _init_storage_status(),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            log.info(
                f"Team Owner 添加到 tracker: {email} -> {team_name} (格式: {team_format}, 状态: {status})"
            )
            added_count += 1

    if added_count > 0:
        log.info(f"已添加 {added_count} 个 Team Owner 到 tracker", icon="sync")

    return added_count
