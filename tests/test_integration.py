# ==================== Workflow Integration Tests ====================
# Test full invited -> completed flow across auth providers.

"""Test integration workflow

Test cases:
    - test_full_flow_crs_provider
    - test_full_flow_cpa_provider
    - test_full_flow_s2a_provider
"""

from unittest.mock import patch

import src.core.workflow as workflow
import src.core.utils as utils
from src.core.storage_manager import init_storage_status


def _make_tracker(team_name: str, email: str) -> dict:
    return {
        "teams": {
            team_name: [
                {
                    "email": email,
                    "invitation_status": "invited",
                    "storage_status": init_storage_status(),
                }
            ]
        },
        "last_updated": None,
    }


def _init_workflow_state(tracker: dict) -> None:
    workflow._tracker = tracker
    workflow._current_results = []
    workflow._shutdown_requested = False


def test_full_flow_crs_provider():
    team_name = "alpha"
    email = "user@example.com"
    tracker = _make_tracker(team_name, email)
    _init_workflow_state(tracker)

    accounts = [
        {
            "email": email,
            "password": "pass-123",
            "invitation_status": "invited",
            "role": "member",
        }
    ]
    codex_data = {"code": "code-1", "session_id": "session-1"}

    with (
        patch("src.core.workflow.AUTH_PROVIDER", "crs"),
        patch("src.core.workflow._get_team_by_name", return_value={}),
        patch("src.core.workflow.is_email_blacklisted", return_value=False),
        patch("src.core.workflow.register_and_authorize", return_value=(True, codex_data)),
        patch("src.core.workflow.check_account_stored", return_value={"exists": False}),
        patch("src.core.workflow.crs_add_account", return_value={"id": "crs-1"}),
        patch("src.core.workflow.save_team_tracker"),
        patch("src.core.workflow.save_to_csv"),
        patch("src.core.workflow.time.sleep"),
        patch("src.core.workflow.random.randint", return_value=0),
        patch(
            "src.core.workflow.update_account_status",
            wraps=utils.update_account_status,
        ) as update_status,
    ):
        results = workflow.process_accounts(accounts, team_name)

    assert results[0]["status"] == "success"
    assert results[0]["crs_id"] == "crs-1"

    status_calls = [call.args[3] for call in update_status.call_args_list]
    assert status_calls == ["processing", "registered", "authorized", "completed"]

    account = tracker["teams"][team_name][0]
    assert account["invitation_status"] == "completed"
    assert account["storage_status"]["crs"]["status"] == "stored"
    assert account["storage_status"]["crs"]["account_id"] == "crs-1"


def test_full_flow_cpa_provider():
    team_name = "alpha"
    email = "user@example.com"
    tracker = _make_tracker(team_name, email)
    _init_workflow_state(tracker)

    accounts = [
        {
            "email": email,
            "password": "pass-123",
            "invitation_status": "invited",
            "role": "member",
        }
    ]

    with (
        patch("src.core.workflow.AUTH_PROVIDER", "cpa"),
        patch("src.core.workflow._get_team_by_name", return_value={}),
        patch("src.core.workflow.is_email_blacklisted", return_value=False),
        patch(
            "src.core.workflow.register_and_authorize",
            return_value=(True, {"code": "code-1", "session_id": "session-1"}),
        ),
        patch("src.core.workflow.check_account_stored", return_value={"exists": False}),
        patch("src.core.workflow.save_team_tracker"),
        patch("src.core.workflow.save_to_csv"),
        patch("src.core.workflow.time.sleep"),
        patch("src.core.workflow.random.randint", return_value=0),
        patch(
            "src.core.workflow.update_account_status",
            wraps=utils.update_account_status,
        ) as update_status,
    ):
        results = workflow.process_accounts(accounts, team_name)

    assert results[0]["status"] == "success"
    assert results[0]["crs_id"] == "CPA-AUTO"

    status_calls = [call.args[3] for call in update_status.call_args_list]
    assert status_calls == ["processing", "registered", "authorized", "completed"]

    account = tracker["teams"][team_name][0]
    assert account["invitation_status"] == "completed"
    assert account["storage_status"]["cpa"]["status"] == "stored"
    assert "account_id" not in account["storage_status"]["cpa"]


def test_full_flow_s2a_provider():
    team_name = "alpha"
    email = "user@example.com"
    tracker = _make_tracker(team_name, email)
    _init_workflow_state(tracker)

    accounts = [
        {
            "email": email,
            "password": "pass-123",
            "invitation_status": "invited",
            "role": "member",
        }
    ]
    codex_data = {"code": "code-1", "session_id": "session-1"}

    with (
        patch("src.core.workflow.AUTH_PROVIDER", "s2a"),
        patch("src.core.workflow._get_team_by_name", return_value={}),
        patch("src.core.workflow.is_email_blacklisted", return_value=False),
        patch("src.core.workflow.register_and_authorize", return_value=(True, codex_data)),
        patch("src.core.workflow.check_account_stored", return_value={"exists": False}),
        patch(
            "src.core.workflow.s2a_create_account_from_oauth",
            return_value={"id": "s2a-1"},
        ),
        patch("src.core.workflow.save_team_tracker"),
        patch("src.core.workflow.save_to_csv"),
        patch("src.core.workflow.time.sleep"),
        patch("src.core.workflow.random.randint", return_value=0),
        patch(
            "src.core.workflow.update_account_status",
            wraps=utils.update_account_status,
        ) as update_status,
    ):
        results = workflow.process_accounts(accounts, team_name)

    assert results[0]["status"] == "success"
    assert results[0]["crs_id"] == "S2A-s2a-1"

    status_calls = [call.args[3] for call in update_status.call_args_list]
    assert status_calls == ["processing", "registered", "authorized", "completed"]

    account = tracker["teams"][team_name][0]
    assert account["invitation_status"] == "completed"
    assert account["storage_status"]["s2a"]["status"] == "stored"
    assert account["storage_status"]["s2a"]["account_id"] == "s2a-1"


def test_token_refresh_success_updates_team_json():
    team_name = "alpha"
    tracker = {"teams": {}, "last_updated": None}
    _init_workflow_state(tracker)

    team = {
        "name": team_name,
        "access_token": "old-access",
        "auth_token": "old-access",
        "refresh_token": "refresh-1",
        "token_expires_at": 0,
        "needs_login": True,
        "authorized": False,
    }
    refreshed = {
        "access_token": "new-access",
        "refresh_token": "refresh-2",
        "token_expires_at": 1730000000,
    }

    with (
        patch("src.core.workflow._get_team_by_name", return_value=team),
        patch("src.core.workflow.is_token_expired", return_value=True),
        patch("src.core.workflow.refresh_access_token", return_value=refreshed) as refresh,
        patch("src.core.workflow.save_team_json", return_value=True) as save_team,
        patch("src.core.workflow.log"),
    ):
        workflow.process_accounts([], team_name)

    refresh.assert_called_once_with("refresh-1")
    save_team.assert_called_once()
    assert team["access_token"] == "new-access"
    assert team["auth_token"] == "new-access"
    assert team["refresh_token"] == "refresh-2"
    assert team["token_expires_at"] == 1730000000
    assert team["needs_login"] is False
    assert team["authorized"] is True


def test_token_refresh_failure_fallback_to_old_token():
    team_name = "alpha"
    tracker = {"teams": {}, "last_updated": None}
    _init_workflow_state(tracker)

    team = {
        "name": team_name,
        "access_token": "old-access",
        "auth_token": "old-access",
        "refresh_token": "refresh-1",
        "token_expires_at": 0,
        "needs_login": True,
        "authorized": False,
    }

    with (
        patch("src.core.workflow._get_team_by_name", return_value=team),
        patch("src.core.workflow.is_token_expired", return_value=True),
        patch("src.core.workflow.refresh_access_token", return_value=None) as refresh,
        patch("src.core.workflow.save_team_json") as save_team,
        patch("src.core.workflow.log"),
    ):
        workflow.process_accounts([], team_name)

    refresh.assert_called_once_with("refresh-1")
    save_team.assert_not_called()
    assert team["access_token"] == "old-access"
    assert team["auth_token"] == "old-access"
    assert team["refresh_token"] == "refresh-1"
    assert team["needs_login"] is True
    assert team["authorized"] is False


def test_token_refresh_missing_refresh_token_warns():
    team_name = "alpha"
    tracker = {"teams": {}, "last_updated": None}
    _init_workflow_state(tracker)

    team = {
        "name": team_name,
        "access_token": "old-access",
        "auth_token": "old-access",
        "token_expires_at": 0,
        "needs_login": True,
        "authorized": False,
    }

    with (
        patch("src.core.workflow._get_team_by_name", return_value=team),
        patch("src.core.workflow.is_token_expired", return_value=True),
        patch("src.core.workflow.refresh_access_token") as refresh,
        patch("src.core.workflow.save_team_json") as save_team,
        patch("src.core.workflow.log.warning") as log_warning,
    ):
        workflow.process_accounts([], team_name)

    refresh.assert_not_called()
    save_team.assert_not_called()
    log_warning.assert_any_call(
        f"Team {team_name} 缺少 refresh_token，无法刷新 Token"
    )
