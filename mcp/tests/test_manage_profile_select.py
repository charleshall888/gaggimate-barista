"""Unit tests for manage_profile(action="select", ...) — spec §§R1–R10.

Mock strategy: patch at the WebSocketClient method level (list_profiles,
load_profile, select_profile). The server module-level ws_client is the
patching target, accessed via patch.object on server.ws_client.

Call style: invoke server.manage_profile() directly as an async function —
matching the pattern in test_save_shot_notes_rmw.py.
"""

import importlib
import json
from unittest.mock import AsyncMock, patch

import pytest

import gaggimate_mcp.server as server
from gaggimate_mcp.errors import ErrorCode, GaggimateError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_PROFILES = [
    {"id": "aaa-111", "label": "Munyinya Light Bloom [AI]", "selected": False},
    {"id": "bbb-222", "label": "Classic 9 Bar", "selected": True},
    {"id": "ccc-333", "label": "Bloom Slide [AI]", "selected": False},
]

TARGET_ID = "aaa-111"
TARGET_LABEL = "Munyinya Light Bloom [AI]"


def _profiles_with_selected(target_id: str) -> list[dict]:
    """Return SAMPLE_PROFILES with exactly target_id marked selected:true."""
    return [
        {**p, "selected": p["id"] == target_id}
        for p in SAMPLE_PROFILES
    ]


# ---------------------------------------------------------------------------
# R2 — accept exactly one of profile_id / profile_name
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_select_resolves_profile_name_to_id():
    """Supplying profile_name resolves to id via list, then calls select with that id."""
    updated_profiles = _profiles_with_selected(TARGET_ID)

    with (
        patch.object(server.ws_client, "list_profiles", new_callable=AsyncMock) as mock_list,
        patch.object(server.ws_client, "load_profile", new_callable=AsyncMock) as mock_load,
        patch.object(server.ws_client, "select_profile", new_callable=AsyncMock) as mock_select,
    ):
        # First call to list_profiles is name resolution; second is post-select refresh.
        mock_list.side_effect = [SAMPLE_PROFILES, updated_profiles]
        mock_load.return_value = {"id": TARGET_ID, "label": TARGET_LABEL}
        mock_select.return_value = {}

        result_json = await server.manage_profile(
            action="select",
            profile_name=TARGET_LABEL,
        )
        result = json.loads(result_json)

    assert result["success"] is True
    # select_profile must have been called with the resolved id, not the label
    mock_select.assert_called_once_with(TARGET_ID)


@pytest.mark.asyncio
async def test_select_rejects_both_id_and_name():
    """Passing both profile_id and profile_name returns invalid_input error."""
    result_json = await server.manage_profile(
        action="select",
        profile_id=TARGET_ID,
        profile_name=TARGET_LABEL,
    )
    result = json.loads(result_json)

    assert result["success"] is False
    assert result["action"] == "select"
    assert result["error_code"] == "invalid_input"
    assert "error" in result
    assert "suggestion" in result


@pytest.mark.asyncio
async def test_select_rejects_neither_id_nor_name():
    """Passing neither profile_id nor profile_name returns invalid_input error."""
    result_json = await server.manage_profile(action="select")
    result = json.loads(result_json)

    assert result["success"] is False
    assert result["action"] == "select"
    assert result["error_code"] == "invalid_input"
    assert "error" in result
    assert "suggestion" in result


# ---------------------------------------------------------------------------
# R3 — pre-validate via load_profile before select
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_select_prevalidates_with_load():
    """load_profile returning None aborts before req:profiles:select is sent."""
    with (
        patch.object(server.ws_client, "load_profile", new_callable=AsyncMock) as mock_load,
        patch.object(server.ws_client, "select_profile", new_callable=AsyncMock) as mock_select,
    ):
        mock_load.return_value = None  # profile not found
        mock_select.return_value = {}

        result_json = await server.manage_profile(
            action="select",
            profile_id="unknown-id",
        )
        result = json.loads(result_json)

    # select must NOT have been called
    assert mock_select.call_count == 0
    assert result["success"] is False
    assert result["action"] == "select"
    assert result["error_code"] == "profile_not_found"
    assert "error" in result
    assert "suggestion" in result


@pytest.mark.asyncio
async def test_select_prevalidate_ws_failure_propagates():
    """load_profile raising WEBSOCKET_ERROR is surfaced as websocket_error response."""
    with (
        patch.object(server.ws_client, "load_profile", new_callable=AsyncMock) as mock_load,
        patch.object(server.ws_client, "select_profile", new_callable=AsyncMock) as mock_select,
    ):
        mock_load.side_effect = GaggimateError(
            ErrorCode.WEBSOCKET_ERROR, "conn refused"
        )
        mock_select.return_value = {}

        result_json = await server.manage_profile(
            action="select",
            profile_id=TARGET_ID,
        )
        result = json.loads(result_json)

    assert result["success"] is False
    assert result["action"] == "select"
    assert result["error_code"] == "websocket_error"
    assert "error" in result
    assert "suggestion" in result
    # select was never reached
    assert mock_select.call_count == 0


# ---------------------------------------------------------------------------
# R5 — happy path: full updated list with verified selection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_select_returns_full_updated_list():
    """Happy path: target profile shows selected:true in post-select list."""
    updated_profiles = _profiles_with_selected(TARGET_ID)

    with (
        patch.object(server.ws_client, "list_profiles", new_callable=AsyncMock) as mock_list,
        patch.object(server.ws_client, "load_profile", new_callable=AsyncMock) as mock_load,
        patch.object(server.ws_client, "select_profile", new_callable=AsyncMock) as mock_select,
    ):
        mock_list.return_value = updated_profiles
        mock_load.return_value = {"id": TARGET_ID, "label": TARGET_LABEL}
        mock_select.return_value = {}

        result_json = await server.manage_profile(
            action="select",
            profile_id=TARGET_ID,
        )
        result = json.loads(result_json)

    assert result["success"] is True
    assert result["action"] == "select"
    assert "profiles" in result
    assert result["count"] == len(updated_profiles)
    assert result["count"] == len(result["profiles"])
    # The target profile must be selected:true in the returned list
    target_entry = next(p for p in result["profiles"] if p["id"] == TARGET_ID)
    assert target_entry["selected"] is True


# ---------------------------------------------------------------------------
# R6 — partial success: select landed, list refetch fails
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_select_partial_success_list_fails():
    """select succeeds but subsequent list_profiles raises → partial success."""
    with (
        patch.object(server.ws_client, "load_profile", new_callable=AsyncMock) as mock_load,
        patch.object(server.ws_client, "select_profile", new_callable=AsyncMock) as mock_select,
        patch.object(server.ws_client, "list_profiles", new_callable=AsyncMock) as mock_list,
    ):
        mock_load.return_value = {"id": TARGET_ID, "label": TARGET_LABEL}
        mock_select.return_value = {}
        mock_list.side_effect = GaggimateError(ErrorCode.API_ERROR, "list failed")

        result_json = await server.manage_profile(
            action="select",
            profile_id=TARGET_ID,
        )
        result = json.loads(result_json)

    assert result["success"] is True
    assert result["selected_profile_id"] == TARGET_ID
    assert result["profiles_refetch_failed"] is True
    assert "profiles" not in result


# ---------------------------------------------------------------------------
# R7 — divergence check
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_select_detects_selection_divergence():
    """Post-select list shows a DIFFERENT profile selected → success:false, api_error."""
    other_id = "bbb-222"
    # Build a list where a DIFFERENT profile is selected (not TARGET_ID)
    diverged_profiles = _profiles_with_selected(other_id)

    with (
        patch.object(server.ws_client, "list_profiles", new_callable=AsyncMock) as mock_list,
        patch.object(server.ws_client, "load_profile", new_callable=AsyncMock) as mock_load,
        patch.object(server.ws_client, "select_profile", new_callable=AsyncMock) as mock_select,
    ):
        mock_list.return_value = diverged_profiles
        mock_load.return_value = {"id": TARGET_ID, "label": TARGET_LABEL}
        mock_select.return_value = {}

        result_json = await server.manage_profile(
            action="select",
            profile_id=TARGET_ID,
        )
        result = json.loads(result_json)

    assert result["success"] is False
    assert result["error_code"] == "api_error"
    assert "Selection divergence" in result["error"]
    assert "profiles" in result


# ---------------------------------------------------------------------------
# R8 — error shape parametrization over all six codes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("error_code,error_enum,mock_target,side_effect_factory", [
    (
        "profile_not_found",
        ErrorCode.PROFILE_NOT_FOUND,
        "load_profile",
        lambda: None,  # returns None, not raises — handled specially below
    ),
    (
        "websocket_error",
        ErrorCode.WEBSOCKET_ERROR,
        "load_profile",
        lambda: GaggimateError(ErrorCode.WEBSOCKET_ERROR, "ws error"),
    ),
    (
        "timeout",
        ErrorCode.TIMEOUT,
        "load_profile",
        lambda: GaggimateError(ErrorCode.TIMEOUT, "timed out"),
    ),
    (
        "parse_error",
        ErrorCode.PARSE_ERROR,
        "load_profile",
        lambda: GaggimateError(ErrorCode.PARSE_ERROR, "bad json"),
    ),
    (
        "api_error",
        ErrorCode.API_ERROR,
        "select_profile",
        lambda: GaggimateError(ErrorCode.API_ERROR, "fw error"),
    ),
    (
        "invalid_input",
        ErrorCode.INVALID_INPUT,
        None,  # triggered by passing both id and name (no mock needed)
        lambda: None,
    ),
])
async def test_select_error_shape_all_codes(
    error_code, error_enum, mock_target, side_effect_factory
):
    """Every failure path carries all five required keys with the correct error_code."""
    effect = side_effect_factory()

    if error_code == "invalid_input":
        # Trigger via bad input — no mocking needed
        result_json = await server.manage_profile(
            action="select",
            profile_id=TARGET_ID,
            profile_name=TARGET_LABEL,
        )
    elif mock_target == "load_profile" and effect is None:
        # profile_not_found: load_profile returns None
        with patch.object(server.ws_client, "load_profile", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = None
            result_json = await server.manage_profile(
                action="select",
                profile_id=TARGET_ID,
            )
    elif mock_target == "load_profile":
        # All other load_profile-level raises
        with patch.object(server.ws_client, "load_profile", new_callable=AsyncMock) as mock_load:
            mock_load.side_effect = effect
            result_json = await server.manage_profile(
                action="select",
                profile_id=TARGET_ID,
            )
    else:
        # select_profile-level raise (api_error)
        with (
            patch.object(server.ws_client, "load_profile", new_callable=AsyncMock) as mock_load,
            patch.object(server.ws_client, "select_profile", new_callable=AsyncMock) as mock_select,
        ):
            mock_load.return_value = {"id": TARGET_ID, "label": TARGET_LABEL}
            mock_select.side_effect = effect
            result_json = await server.manage_profile(
                action="select",
                profile_id=TARGET_ID,
            )

    result = json.loads(result_json)

    # All five fields must be present
    assert "success" in result, f"missing 'success' for code={error_code}"
    assert "action" in result, f"missing 'action' for code={error_code}"
    assert "error" in result, f"missing 'error' for code={error_code}"
    assert "error_code" in result, f"missing 'error_code' for code={error_code}"
    assert "suggestion" in result, f"missing 'suggestion' for code={error_code}"

    assert result["success"] is False
    assert result["action"] == "select"
    assert result["error_code"] == error_code


# ---------------------------------------------------------------------------
# R10 — unknown action error message includes "select"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_manage_profile_unknown_action_lists_select():
    """Calling manage_profile with an unknown action returns an error mentioning 'select'."""
    result_json = await server.manage_profile(action="bogus")
    result = json.loads(result_json)

    assert result["success"] is False
    assert "select" in result["error"]
