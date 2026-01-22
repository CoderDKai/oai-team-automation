# ==================== Token 管理模块 ====================
# Token 提取、刷新和更新功能

"""Token Manager - 管理 OAuth Token 的提取、刷新和更新

Functions:
    extract_tokens_from_response: 从 OAuth 响应中提取 token 信息
    is_token_expired: 检查 token 是否已过期
    refresh_access_token: 使用 refresh_token 刷新 access_token
    update_team_tokens: 更新 team.json 中的 token 信息
"""

from __future__ import annotations

import os
import time
from typing import Any

import requests

from src.core.config import (
    REQUEST_TIMEOUT,
    USER_AGENT,
    PROXY_ENABLED,
    get_proxy_dict,
    get_teams,
    save_team_json,
)
from src.core.logger import log


OPENAI_OAUTH_TOKEN_URL = os.getenv(
    "OPENAI_OAUTH_TOKEN_URL", "https://auth.openai.com/oauth/token"
)
OPENAI_OAUTH_CLIENT_ID = os.getenv("OPENAI_OAUTH_CLIENT_ID", "")
OPENAI_OAUTH_CLIENT_SECRET = os.getenv("OPENAI_OAUTH_CLIENT_SECRET", "")
OPENAI_OAUTH_AUDIENCE = os.getenv("OPENAI_OAUTH_AUDIENCE", "")
OPENAI_OAUTH_SCOPE = os.getenv("OPENAI_OAUTH_SCOPE", "")


def _parse_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def extract_tokens_from_response(response: dict) -> dict:
    """从 OAuth 响应中提取 token 信息"""
    if not isinstance(response, dict):
        log.warning("OAuth 响应不是 dict，无法提取 token")
        return {
            "access_token": None,
            "refresh_token": None,
            "token_expires_at": None,
            "id_token": None,
        }

    source = response.get("tokens") if isinstance(response.get("tokens"), dict) else response

    access_token = (
        source.get("access_token")
        or source.get("accessToken")
        or response.get("access_token")
        or response.get("accessToken")
        or source.get("token")
    )
    refresh_token = (
        source.get("refresh_token")
        or source.get("refreshToken")
        or response.get("refresh_token")
        or response.get("refreshToken")
    )
    id_token = (
        source.get("id_token")
        or source.get("idToken")
        or response.get("id_token")
        or response.get("idToken")
    )

    token_expires_at = (
        source.get("token_expires_at")
        or source.get("tokenExpiresAt")
        or source.get("expires_at")
        or response.get("token_expires_at")
        or response.get("tokenExpiresAt")
        or response.get("expires_at")
    )

    expires_in = (
        source.get("expires_in")
        or source.get("expiresIn")
        or response.get("expires_in")
        or response.get("expiresIn")
    )

    token_expires_at = _parse_int(token_expires_at)
    expires_in = _parse_int(expires_in)

    if token_expires_at is None and expires_in is not None:
        token_expires_at = int(time.time()) + expires_in

    if not access_token:
        log.warning("OAuth 响应缺少 access_token")
    if not refresh_token:
        log.warning("OAuth 响应缺少 refresh_token")
    if token_expires_at is None and expires_in is None:
        log.warning("OAuth 响应缺少过期信息")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_expires_at": token_expires_at,
        "id_token": id_token,
    }


def is_token_expired(expires_at: int, buffer_seconds: int = 3600) -> bool:
    """检查 token 是否过期或即将过期"""
    expires_at_value = _parse_int(expires_at)
    if not expires_at_value:
        return True
    return expires_at_value <= int(time.time()) + int(buffer_seconds)


def refresh_access_token(refresh_token: str, provider: str = "openai") -> dict | None:
    """使用 refresh_token 刷新 access_token"""
    if not refresh_token:
        log.warning("refresh_token 为空，无法刷新 access_token")
        return None

    if provider != "openai":
        log.warning(f"暂不支持的 OAuth provider: {provider}")
        return None

    payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    if OPENAI_OAUTH_CLIENT_ID:
        payload["client_id"] = OPENAI_OAUTH_CLIENT_ID
    if OPENAI_OAUTH_CLIENT_SECRET:
        payload["client_secret"] = OPENAI_OAUTH_CLIENT_SECRET
    if OPENAI_OAUTH_AUDIENCE:
        payload["audience"] = OPENAI_OAUTH_AUDIENCE
    if OPENAI_OAUTH_SCOPE:
        payload["scope"] = OPENAI_OAUTH_SCOPE

    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": USER_AGENT,
    }

    proxies = get_proxy_dict() if PROXY_ENABLED else None

    try:
        response = requests.post(
            OPENAI_OAUTH_TOKEN_URL,
            data=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            proxies=proxies,
        )
    except Exception as exc:
        log.error(f"刷新 access_token 异常: {exc}")
        return None

    if response.status_code != 200:
        log.error(f"刷新 access_token 失败: HTTP {response.status_code}")
        try:
            error_detail = response.json()
            log.warning(f"错误详情: {error_detail}")
        except Exception:
            try:
                log.warning(f"响应内容: {response.text[:200]}")
            except Exception:
                pass
        return None

    try:
        result = response.json()
    except Exception as exc:
        log.error(f"解析刷新响应失败: {exc}")
        return None

    tokens = extract_tokens_from_response(result)
    if not tokens.get("access_token"):
        log.warning("刷新响应未返回 access_token")
        return None

    log.success("access_token 刷新成功")
    return tokens


def update_team_tokens(team_index: int, tokens: dict) -> bool:
    """更新 team.json 中的 token 信息"""
    teams = get_teams()
    if team_index < 0 or team_index >= len(teams):
        log.error(f"Team 索引超出范围 (0-{len(teams) - 1})")
        return False

    if not isinstance(tokens, dict):
        log.error("tokens 参数格式错误，必须是 dict")
        return False

    token_data = extract_tokens_from_response(tokens)
    team = teams[team_index]

    if team.get("format") != "new":
        log.warning("仅支持更新新格式的 Team 配置")
        return False

    updated = False

    access_token = token_data.get("access_token")
    if access_token and team.get("access_token") != access_token:
        team["access_token"] = access_token
        team["auth_token"] = access_token
        team["needs_login"] = False
        updated = True

    refresh_token = token_data.get("refresh_token")
    if refresh_token and team.get("refresh_token") != refresh_token:
        team["refresh_token"] = refresh_token
        updated = True

    token_expires_at = token_data.get("token_expires_at")
    if token_expires_at and team.get("token_expires_at") != token_expires_at:
        team["token_expires_at"] = token_expires_at
        updated = True

    if access_token:
        team["authorized"] = True

    if not updated:
        log.warning("Team token 未发生变化，跳过保存")
        return False

    if save_team_json():
        log.success("Team token 已保存到 team.json")
        return True

    log.error("保存 team.json 失败")
    return False
