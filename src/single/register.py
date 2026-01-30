from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.core.logger import log


def _default_password() -> str:
    from src.core.config import DEFAULT_PASSWORD

    return DEFAULT_PASSWORD


def _normalize_accounts(raw: Any) -> list[dict]:
    accounts: list[dict] = []

    if isinstance(raw, dict) and "accounts" in raw:
        raw = raw.get("accounts", [])

    if not isinstance(raw, list):
        log.error("accounts.json 格式无效，应为数组或包含 accounts 字段的对象")
        return accounts

    default_password = _default_password()

    for index, item in enumerate(raw, start=1):
        email = ""
        password = default_password

        if isinstance(item, str):
            email = item.strip()
        elif isinstance(item, dict):
            email = str(item.get("email") or item.get("account") or "").strip()
            password = str(item.get("password") or default_password).strip()
        else:
            log.warning(f"第 {index} 项格式不支持，已跳过")
            continue

        if not email:
            log.warning(f"第 {index} 项缺少邮箱，已跳过")
            continue

        accounts.append({"email": email, "password": password})

    return accounts


def _parse_accounts_payload(raw: Any) -> list[dict]:
    accounts = _normalize_accounts(raw)
    if not accounts:
        log.warning("accounts.json 未包含可用账号")
    return accounts


def load_accounts_source(source: str) -> list[dict]:
    if not source:
        log.error("未提供账号来源 (--file)")
        return []

    raw_text = source.strip()
    if raw_text.startswith("{") or raw_text.startswith("["):
        try:
            raw = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            log.error(f"JSON 字符串解析失败: {exc}")
            return []
        return _parse_accounts_payload(raw)

    path = Path(raw_text)
    if not path.exists():
        log.error(f"未找到账号文件: {path}")
        return []

    try:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as exc:
        log.error(f"账号文件解析失败: {exc}")
        return []
    except Exception as exc:
        log.error(f"读取账号文件失败: {exc}")
        return []

    return _parse_accounts_payload(raw)


def _register_single_account(email: str, password: str) -> bool | str:
    try:
        from src.automation.browser import (
            browser_context_with_retry,
            register_openai_account,
        )
    except ModuleNotFoundError as exc:
        log.error(f"缺少依赖模块: {exc.name}，请先安装 requirements.txt")
        return "dependency_missing"

    with browser_context_with_retry(max_browser_retries=2) as ctx:
        for attempt in ctx.attempts():
            try:
                result = register_openai_account(ctx.page, email, password)
                if result == "domain_blacklisted":
                    ctx.stop()
                    return "domain_blacklisted"
                if result:
                    return True
                if attempt < ctx.max_retries - 1:
                    log.warning("注册失败，准备重试...")
                    continue
                ctx.capture_failure("register_failed")
                return False
            except Exception as exc:
                ctx.handle_error(exc)
                if ctx.current_attempt >= ctx.max_retries - 1:
                    return False

    return False


def register_from_source(source: str) -> int:
    from src.core.utils import Timer, save_to_csv
    from src.core.config import (
        add_domain_to_blacklist,
        get_domain_from_email,
        is_email_blacklisted,
    )

    accounts = load_accounts_source(source)
    if not accounts:
        return 1

    total = len(accounts)
    results: list[dict] = []
    failed = 0

    log.header(f"开始注册账号，共 {total} 个")

    for index, account in enumerate(accounts, start=1):
        email = account["email"]
        password = account["password"]

        if is_email_blacklisted(email):
            log.warning(f"邮箱域名已在黑名单中，跳过: {email}")
            results.append({"email": email, "status": "domain_blacklisted"})
            failed += 1
            continue

        log.section(f"账号 {index}/{total}: {email}")
        with Timer(f"注册账号 {email}"):
            result = _register_single_account(email, password)

        if result == "dependency_missing":
            return 1

        if result == "domain_blacklisted":
            domain = get_domain_from_email(email)
            add_domain_to_blacklist(domain)
            log.error(f"邮箱域名不被支持: {domain}")
            status = "domain_blacklisted"
            failed += 1
        elif result:
            log.success(f"注册成功: {email}")
            status = "success"
        else:
            log.error(f"注册失败: {email}")
            status = "failed"
            failed += 1

        save_to_csv(email=email, password=password, status=status)
        results.append({"email": email, "status": status})

    success = total - failed
    log.separator("-", 40)
    log.info(f"注册完成: {success}/{total} 成功")

    return 0 if failed == 0 else 1
