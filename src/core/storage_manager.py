# ==================== 入库状态管理模块 ====================
# 入库状态初始化、查询和更新功能

"""Storage Manager - 管理账号入库状态

Functions:
    init_storage_status: 初始化入库状态结构
    get_enabled_providers: 获取已启用的服务商列表
    check_account_stored: 查询账号在指定服务商中的入库状态
    update_storage_status: 更新 team_tracker.json 中的入库状态
"""

from __future__ import annotations

from datetime import datetime

from src.auth.cpa.client import cpa_query_account
from src.auth.crs.client import crs_query_account
from src.auth.s2a.client import s2a_get_accounts
from src.core.config import (
    CPA_ADMIN_PASSWORD,
    CPA_API_BASE,
    CRS_ADMIN_TOKEN,
    CRS_API_BASE,
    S2A_ADMIN_KEY,
    S2A_API_BASE,
)
from src.core.logger import log


def init_storage_status() -> dict:
    """初始化入库状态结构"""
    return {
        "crs": {"status": "not_stored"},
        "cpa": {"status": "not_stored"},
        "s2a": {"status": "not_stored"},
    }


def _is_configured(value: str | None) -> bool:
    return bool(value and str(value).strip())


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _normalize_provider(provider: str) -> str:
    return (provider or "").strip().lower()


def _s2a_query_account(email: str) -> dict:
    target_email = (email or "").lower()
    if not target_email:
        return {"exists": False, "account_id": None}

    accounts = s2a_get_accounts("openai")
    for account in accounts:
        account_name = (account.get("name") or "").lower()
        credentials = account.get("credentials") or {}
        account_email = (credentials.get("email") or "").lower()
        if account_name == target_email or account_email == target_email:
            return {
                "exists": True,
                "account_id": account.get("id") or account.get("account_id"),
            }

    return {"exists": False, "account_id": None}


def get_enabled_providers() -> list[str]:
    """获取已启用的服务商列表"""
    providers = []
    if _is_configured(CRS_API_BASE) and _is_configured(CRS_ADMIN_TOKEN):
        providers.append("crs")
    if _is_configured(CPA_API_BASE) and _is_configured(CPA_ADMIN_PASSWORD):
        providers.append("cpa")
    if _is_configured(S2A_API_BASE) and _is_configured(S2A_ADMIN_KEY):
        providers.append("s2a")
    return providers


def check_account_stored(email: str, provider: str) -> dict:
    """查询账号在指定服务商中的入库状态"""
    last_check = _now_str()
    provider_key = _normalize_provider(provider)

    if not email or not provider_key:
        return {"exists": False, "account_id": None, "last_check": last_check}

    try:
        log.info(f"开始查询入库状态: provider={provider_key}, email={email}")
        if provider_key == "crs":
            result = crs_query_account(email)
        elif provider_key == "cpa":
            result = cpa_query_account(email)
        elif provider_key == "s2a":
            result = _s2a_query_account(email)
        else:
            log.warning(f"未知服务商: {provider}")
            return {"exists": False, "account_id": None, "last_check": last_check}

        exists = bool(result.get("exists"))
        log.info(
            f"查询入库状态结果: provider={provider_key}, email={email}, exists={exists}"
        )
        return {
            "exists": exists,
            "account_id": result.get("account_id"),
            "last_check": last_check,
        }
    except Exception as e:
        log.warning(f"查询入库状态失败 ({provider}): {e}")
        return {"exists": False, "account_id": None, "last_check": last_check}


def update_storage_status(
    tracker: dict,
    team_name: str,
    email: str,
    provider: str,
    status_data: dict,
) -> None:
    """更新 tracker 中指定账号的入库状态"""
    provider_key = _normalize_provider(provider)
    if not provider_key:
        return

    teams = tracker.get("teams")
    if not isinstance(teams, dict):
        return

    if team_name not in teams:
        return

    for account in teams[team_name]:
        if account.get("email") != email:
            continue

        log.info(
            f"更新入库状态: team={team_name}, email={email}, provider={provider_key}"
        )
        if not isinstance(account.get("storage_status"), dict):
            account["storage_status"] = init_storage_status()

        if provider_key not in account["storage_status"]:
            account["storage_status"][provider_key] = {"status": "not_stored"}

        provider_status = account["storage_status"][provider_key]
        explicit_status = status_data.get("status")
        exists = status_data.get("exists")

        if explicit_status:
            provider_status["status"] = explicit_status
        elif exists is not None:
            provider_status["status"] = "stored" if exists else "not_stored"

        if "account_id" in status_data:
            provider_status["account_id"] = status_data.get("account_id")
        if "last_check" in status_data:
            provider_status["last_check"] = status_data.get("last_check")

        account["updated_at"] = _now_str()
        log.info(
            "入库状态更新完成: "
            f"team={team_name}, email={email}, provider={provider_key}, "
            f"status={provider_status.get('status')}"
        )
        return
