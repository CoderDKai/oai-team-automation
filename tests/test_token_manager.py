# ==================== Token Manager 测试 ====================
# 测试 Token 提取、刷新和更新功能

"""Test Token Manager

测试用例:
    - test_extract_tokens_from_response: 测试 token 提取
    - test_is_token_expired: 测试过期检查
    - test_refresh_access_token: 测试 token 刷新
    - test_update_team_tokens: 测试 token 更新
"""

import json
from unittest.mock import Mock, patch

from src.auth.token_manager import (
    extract_tokens_from_response,
    is_token_expired,
    refresh_access_token,
    update_team_tokens,
)


def test_extract_tokens_from_response():
    fixed_now = 1_700_000_000
    response = {
        "access_token": "access-123",
        "refresh_token": "refresh-456",
        "id_token": "id-789",
        "expires_in": 7200,
    }

    with patch("src.auth.token_manager.time.time", return_value=fixed_now):
        tokens = extract_tokens_from_response(response)

    assert tokens["access_token"] == "access-123"
    assert tokens["refresh_token"] == "refresh-456"
    assert tokens["id_token"] == "id-789"
    assert tokens["token_expires_at"] == fixed_now + 7200

    with patch("src.auth.token_manager.time.time", return_value=fixed_now):
        empty_tokens = extract_tokens_from_response({})

    assert "access_token" in empty_tokens
    assert "refresh_token" in empty_tokens
    assert "id_token" in empty_tokens
    assert "token_expires_at" in empty_tokens
    assert not empty_tokens["access_token"]
    assert not empty_tokens["refresh_token"]
    assert not empty_tokens["id_token"]
    assert not empty_tokens["token_expires_at"]


def test_is_token_expired():
    fixed_now = 1_700_000_000
    with patch("src.auth.token_manager.time.time", return_value=fixed_now):
        assert is_token_expired(fixed_now + 7200, buffer_seconds=3600) is False
        assert is_token_expired(fixed_now + 3600, buffer_seconds=3600) is True
        assert is_token_expired(fixed_now + 10, buffer_seconds=3600) is True
        assert is_token_expired(0, buffer_seconds=3600) is True


def test_refresh_access_token():
    fixed_now = 1_700_000_000
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "new-access",
        "refresh_token": "new-refresh",
        "id_token": "new-id",
        "expires_in": 3600,
    }

    with patch("src.auth.token_manager.requests.post", return_value=mock_response):
        with patch("src.auth.token_manager.time.time", return_value=fixed_now):
            tokens = refresh_access_token("refresh-token", provider="openai")

    assert tokens["access_token"] == "new-access"
    assert tokens["refresh_token"] == "new-refresh"
    assert tokens["id_token"] == "new-id"
    assert tokens["token_expires_at"] == fixed_now + 3600

    error_response = Mock()
    error_response.status_code = 400
    error_response.json.return_value = {}

    with patch("src.auth.token_manager.requests.post", return_value=error_response):
        assert refresh_access_token("refresh-token", provider="openai") is None


def test_update_team_tokens(tmp_path, monkeypatch):
    team_file = tmp_path / "team.json"
    teams = [
        {
            "account": "owner@example.com",
            "token": "old-access",
            "access_token": "old-access",
            "refresh_token": "old-refresh",
            "token_expires_at": 100,
        },
        {"account": "other@example.com"},
    ]
    team_file.write_text(json.dumps(teams), encoding="utf-8")

    import src.auth.token_manager as token_manager
    import src.core.config as config

    monkeypatch.setattr(token_manager, "BASE_DIR", tmp_path, raising=False)
    monkeypatch.setattr(token_manager, "TEAM_JSON_FILE", team_file, raising=False)
    monkeypatch.setattr(config, "BASE_DIR", tmp_path, raising=False)
    monkeypatch.setattr(config, "TEAM_JSON_FILE", team_file, raising=False)
    monkeypatch.setattr(config, "_raw_teams", None, raising=False)
    monkeypatch.setattr(config, "_teams_loaded", False, raising=False)
    monkeypatch.setattr(config, "TEAMS", [], raising=False)

    tokens = {
        "access_token": "new-access",
        "refresh_token": "new-refresh",
        "token_expires_at": 123,
        "id_token": "new-id",
    }

    assert update_team_tokens(0, tokens) is True

    updated = json.loads(team_file.read_text(encoding="utf-8"))
    assert updated[0]["access_token"] == "new-access"
    assert updated[0]["refresh_token"] == "new-refresh"
    assert updated[0]["token_expires_at"] == 123
    assert updated[0]["token"] == "new-access"

    assert update_team_tokens(99, tokens) is False
