"""创建 Team 父账号模块

功能：
1. 注册 OpenAI 账号
2. 订阅 ChatGPT Team
3. 创建工作区
4. 保存账号信息到 team.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.core.logger import log


# ==================== 美国州缩写映射表 ====================
US_STATE_MAPPING = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AS": "American Samoa",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "AA": "Armed Forces (AA)",
    "AE": "Armed Forces (AE)",
    "AP": "Armed Forces (AP)",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "District of Columbia",
    "FL": "Florida",
    "GA": "Georgia",
    "GU": "Guam",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MH": "Marshall Islands",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "FM": "Micronesia",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "MP": "Northern Mariana Islands",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PW": "Palau",
    "PA": "Pennsylvania",
    "PR": "Puerto Rico",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VI": "Virgin Islands",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
}


def _default_password() -> str:
    from src.core.config import DEFAULT_PASSWORD
    return DEFAULT_PASSWORD


def parse_address(address: str) -> dict:
    """解析地址字符串

    地址格式示例: "8280 Mayfern Drive, Fairburn, GA 30213, US"

    Returns:
        dict: {
            "line1": "8280 Mayfern Drive",
            "city": "Fairburn",
            "state": "GA",
            "zip": "30213",
            "country": "US"
        }
    """
    parts = [p.strip() for p in address.split(",")]

    result = {
        "line1": "",
        "city": "",
        "state": "",
        "zip": "",
        "country": "US",
    }

    if len(parts) >= 1:
        result["line1"] = parts[0]

    if len(parts) >= 2:
        result["city"] = parts[1]

    if len(parts) >= 3:
        # 解析 "GA 30213" 格式
        state_zip = parts[2].strip().split()
        if len(state_zip) >= 1:
            result["state"] = state_zip[0]
        if len(state_zip) >= 2:
            result["zip"] = state_zip[1]

    if len(parts) >= 4:
        result["country"] = parts[3]

    return result


def _normalize_accounts(raw: Any) -> list[dict]:
    """规范化账号数据格式

    支持的格式:
    1. 数组格式: [{"email": "...", "password": "...", "card_info": {...}}]
    2. 对象格式: {"accounts": [...]}
    """
    accounts: list[dict] = []

    if isinstance(raw, dict) and "accounts" in raw:
        raw = raw.get("accounts", [])

    if not isinstance(raw, list):
        log.error("账号数据格式无效，应为数组或包含 accounts 字段的对象")
        return accounts

    default_password = _default_password()

    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            log.warning(f"第 {index} 项格式不支持，已跳过")
            continue

        email = str(item.get("email") or item.get("account") or "").strip()
        password = str(item.get("password") or default_password).strip()
        card_info = item.get("card_info", {})

        if not email:
            log.warning(f"第 {index} 项缺少邮箱，已跳过")
            continue

        if not card_info:
            log.warning(f"第 {index} 项缺少 card_info，已跳过")
            continue

        accounts.append({
            "email": email,
            "password": password,
            "card_info": card_info,
        })

    return accounts


def load_accounts_source(source: str) -> list[dict]:
    """加载账号数据源

    Args:
        source: JSON 文件路径或 JSON 字符串

    Returns:
        list[dict]: 账号列表
    """
    if not source:
        log.error("未提供账号来源 (--file)")
        return []

    raw_text = source.strip()

    # 尝试解析为 JSON 字符串
    if raw_text.startswith("{") or raw_text.startswith("["):
        try:
            raw = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            log.error(f"JSON 字符串解析失败: {exc}")
            return []
        return _normalize_accounts(raw)

    # 作为文件路径处理
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

    return _normalize_accounts(raw)


def _create_single_parent_account(
    email: str,
    password: str,
    card_info: dict,
) -> bool | str:
    """创建单个 Team 父账号

    Args:
        email: 邮箱地址
        password: 密码
        card_info: 信用卡信息

    Returns:
        bool | str: 成功返回 True，失败返回 False 或错误类型
    """
    try:
        from src.automation.browser import (
            browser_context_with_retry,
            register_openai_account,
            subscribe_chatgpt_team,
        )
    except ModuleNotFoundError as exc:
        log.error(f"缺少依赖模块: {exc.name}，请先安装 requirements.txt")
        return "dependency_missing"

    with browser_context_with_retry(max_browser_retries=2) as ctx:
        for attempt in ctx.attempts():
            try:
                # 步骤1: 注册 OpenAI 账号
                log.section(f"步骤 1: 注册 OpenAI 账号")
                result = register_openai_account(ctx.page, email, password)
                if result == "domain_blacklisted":
                    ctx.stop()
                    return "domain_blacklisted"
                if not result:
                    if attempt < ctx.max_retries - 1:
                        log.warning("注册失败，准备重试...")
                        continue
                    ctx.capture_failure("register_failed")
                    return False

                # 步骤2: 订阅 ChatGPT Team
                log.section(f"步骤 2: 订阅 ChatGPT Team")
                team_result = subscribe_chatgpt_team(
                    ctx.page, email, card_info
                )
                if not team_result:
                    if attempt < ctx.max_retries - 1:
                        log.warning("订阅失败，准备重试...")
                        continue
                    ctx.capture_failure("subscribe_failed")
                    return False

                return team_result

            except Exception as exc:
                ctx.handle_error(exc)
                if ctx.current_attempt >= ctx.max_retries - 1:
                    return False

    return False


def save_to_team_json(email: str, password: str, account_id: str = "") -> bool:
    """保存账号信息到 team.json

    Args:
        email: 邮箱地址
        password: 密码
        account_id: 账户 ID (可选)

    Returns:
        bool: 是否保存成功
    """
    from src.core.config import TEAM_JSON_FILE

    # 构建新的 team 配置
    new_team = {
        "account": email,
        "password": password,
        "authorized": False,
        "account_id": account_id,
        "expires_at": 0,
        "can_receive_verification_code": True,
    }

    try:
        # 读取现有配置
        teams = []
        if TEAM_JSON_FILE.exists():
            with open(TEAM_JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                teams = data if isinstance(data, list) else [data]

        # 添加新配置
        teams.append(new_team)

        # 保存
        with open(TEAM_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(teams, f, ensure_ascii=False, indent=2)

        log.success(f"已保存到 team.json: {email}")
        return True

    except Exception as exc:
        log.error(f"保存 team.json 失败: {exc}")
        return False


def create_parent_accounts_from_source(source: str) -> int:
    """从数据源创建 Team 父账号

    Args:
        source: JSON 文件路径或 JSON 字符串

    Returns:
        int: 退出码 (0=成功, 1=失败)
    """
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

    log.header(f"开始创建 Team 父账号，共 {total} 个")

    for index, account in enumerate(accounts, start=1):
        email = account["email"]
        password = account["password"]
        card_info = account["card_info"]

        if is_email_blacklisted(email):
            log.warning(f"邮箱域名已在黑名单中，跳过: {email}")
            results.append({"email": email, "status": "domain_blacklisted"})
            failed += 1
            continue

        log.section(f"账号 {index}/{total}: {email}")
        with Timer(f"创建 Team 父账号 {email}"):
            result = _create_single_parent_account(email, password, card_info)

        if result == "dependency_missing":
            return 1

        if result == "domain_blacklisted":
            domain = get_domain_from_email(email)
            add_domain_to_blacklist(domain)
            log.error(f"邮箱域名不被支持: {domain}")
            status = "domain_blacklisted"
            failed += 1
        elif result:
            log.success(f"创建成功: {email}")
            status = "success"
            # 保存到 team.json
            save_to_team_json(email, password)
        else:
            log.error(f"创建失败: {email}")
            status = "failed"
            failed += 1

        save_to_csv(email=email, password=password, status=status)
        results.append({"email": email, "status": status})

    success = total - failed
    log.separator("-", 40)
    log.info(f"创建完成: {success}/{total} 成功")

    return 0 if failed == 0 else 1
