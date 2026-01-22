# ==================== Storage Manager 测试 ====================
# 测试入库状态管理功能

"""Test Storage Manager

测试用例:
    - test_init_storage_status: 测试状态初始化
    - test_get_enabled_providers: 测试获取启用的服务商
    - test_check_account_stored: 测试入库状态查询
    - test_update_storage_status: 测试状态更新
"""

from unittest.mock import Mock, patch

from src.core.storage_manager import (
    _s2a_query_account,
    check_account_stored,
    get_enabled_providers,
    init_storage_status,
    update_storage_status,
)
from src.auth.crs.client import crs_query_account
from src.auth.cpa.client import cpa_query_account


def test_init_storage_status():
    status = init_storage_status()

    assert set(status.keys()) == {"crs", "cpa", "s2a"}
    assert status["crs"]["status"] == "not_stored"
    assert status["cpa"]["status"] == "not_stored"
    assert status["s2a"]["status"] == "not_stored"


def test_get_enabled_providers():
    import src.core.storage_manager as storage_manager

    with (
        patch.object(storage_manager, "CRS_API_BASE", "https://crs.example.com"),
        patch.object(storage_manager, "CRS_ADMIN_TOKEN", "token"),
        patch.object(storage_manager, "CPA_API_BASE", ""),
        patch.object(storage_manager, "CPA_ADMIN_PASSWORD", None),
        patch.object(storage_manager, "S2A_API_BASE", "https://s2a.example.com"),
        patch.object(storage_manager, "S2A_ADMIN_KEY", "key"),
    ):
        providers = get_enabled_providers()

    assert providers == ["crs", "s2a"]


def test_check_account_stored():
    fixed_now = "2024-01-01 00:00:00"
    with patch("src.core.storage_manager._now_str", return_value=fixed_now):
        with patch(
            "src.core.storage_manager.crs_query_account",
            return_value={"exists": True, "account_id": "acc-1"},
        ):
            result = check_account_stored("User@example.com", "crs")

    assert result == {
        "exists": True,
        "account_id": "acc-1",
        "last_check": fixed_now,
    }


def test_update_storage_status():
    tracker = {
        "teams": {
            "alpha": [
                {"email": "owner@example.com"},
                {
                    "email": "other@example.com",
                    "storage_status": {"crs": {"status": "not_stored"}},
                },
            ]
        }
    }
    fixed_now = "2024-01-02 00:00:00"

    with patch("src.core.storage_manager._now_str", return_value=fixed_now):
        update_storage_status(
            tracker,
            "alpha",
            "owner@example.com",
            "crs",
            {
                "exists": True,
                "account_id": "acc-1",
                "last_check": "2024-01-01 00:00:00",
            },
        )

    updated = tracker["teams"]["alpha"][0]
    assert updated["storage_status"]["crs"]["status"] == "stored"
    assert updated["storage_status"]["crs"]["account_id"] == "acc-1"
    assert updated["storage_status"]["crs"]["last_check"] == "2024-01-01 00:00:00"
    assert updated["storage_status"]["cpa"]["status"] == "not_stored"
    assert updated["storage_status"]["s2a"]["status"] == "not_stored"
    assert updated["updated_at"] == fixed_now

    untouched = tracker["teams"]["alpha"][1]
    assert untouched["storage_status"]["crs"]["status"] == "not_stored"


def test_s2a_query_account_exists():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "code": 0,
        "data": {
            "items": [
                {
                    "id": "acc-1",
                    "name": "user@example.com",
                    "credentials": {"email": "user@example.com"},
                }
            ]
        },
    }

    with (
        patch("src.auth.s2a.client.http_session.get", return_value=response),
        patch("src.auth.s2a.client.S2A_API_BASE", "https://s2a.example.com"),
    ):
        result = _s2a_query_account("User@example.com")

    assert result == {"exists": True, "account_id": "acc-1"}


def test_s2a_query_account_not_exists():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "code": 0,
        "data": {
            "items": [
                {
                    "id": "acc-2",
                    "name": "other@example.com",
                    "credentials": {"email": "other@example.com"},
                }
            ]
        },
    }

    with (
        patch("src.auth.s2a.client.http_session.get", return_value=response),
        patch("src.auth.s2a.client.S2A_API_BASE", "https://s2a.example.com"),
    ):
        result = _s2a_query_account("user@example.com")

    assert result == {"exists": False, "account_id": None}


def test_s2a_query_account_api_failure():
    with (
        patch("src.auth.s2a.client.http_session.get", side_effect=Exception("boom")),
        patch("src.auth.s2a.client.S2A_API_BASE", "https://s2a.example.com"),
    ):
        result = _s2a_query_account("user@example.com")

    assert result == {"exists": False, "account_id": None}


def test_crs_query_account_exists():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "data": [{"id": "acc-1", "name": "user@example.com"}],
    }

    with patch("src.auth.crs.client.http_session.get", return_value=response):
        result = crs_query_account("User@example.com")

    assert result == {
        "exists": True,
        "account_id": "acc-1",
        "account_data": {"id": "acc-1", "name": "user@example.com"},
    }


def test_crs_query_account_not_exists():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "data": [{"id": "acc-2", "name": "other@example.com"}],
    }

    with patch("src.auth.crs.client.http_session.get", return_value=response):
        result = crs_query_account("user@example.com")

    assert result == {"exists": False, "account_id": None, "account_data": None}


def test_crs_query_account_api_failure():
    with patch("src.auth.crs.client.http_session.get", side_effect=Exception("boom")):
        result = crs_query_account("user@example.com")

    assert result == {"exists": False, "account_id": None, "account_data": None}


def test_cpa_query_account_exists():
    response = Mock()
    response.status_code = 200
    response.json.return_value = [
        {"id": "acc-1", "email": "user@example.com"},
    ]

    with patch("src.auth.cpa.client.http_session.get", return_value=response):
        result = cpa_query_account("User@example.com")

    assert result == {
        "exists": True,
        "account_id": "acc-1",
        "account_data": {"id": "acc-1", "email": "user@example.com"},
    }


def test_cpa_query_account_not_exists():
    response = Mock()
    response.status_code = 200
    response.json.return_value = [
        {"id": "acc-2", "email": "other@example.com"},
    ]

    with patch("src.auth.cpa.client.http_session.get", return_value=response):
        result = cpa_query_account("user@example.com")

    assert result == {"exists": False, "account_id": None, "account_data": None}


def test_cpa_query_account_api_failure():
    with patch("src.auth.cpa.client.http_session.get", side_effect=Exception("boom")):
        result = cpa_query_account("user@example.com")

    assert result == {"exists": False, "account_id": None, "account_data": None}
