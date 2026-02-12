"""Tests for WebSocket client shot notes methods."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from gaggimate_mcp.api.websocket import GaggimateWebSocketClient, generate_request_id
from gaggimate_mcp.config import GaggimateConfig
from gaggimate_mcp.errors import GaggimateError, ErrorCode


class TestGenerateRequestId:
    """Tests for request ID generation."""

    def test_generate_request_id_format(self):
        """Request ID should have correct format."""
        request_id = generate_request_id()
        assert request_id.startswith("mcp-")
        parts = request_id.split("-")
        assert len(parts) == 3
        # Timestamp part should be numeric
        assert parts[1].isdigit()
        # Random suffix should be alphanumeric
        assert parts[2].isalnum()
        assert len(parts[2]) == 9

    def test_generate_request_id_unique(self):
        """Request IDs should be unique."""
        ids = [generate_request_id() for _ in range(100)]
        assert len(set(ids)) == 100


class TestWebSocketClientShotNotes:
    """Tests for shot notes WebSocket methods."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return GaggimateConfig(gaggimate_host="test.local")

    @pytest.fixture
    def client(self, config):
        """Create WebSocket client with test config."""
        return GaggimateWebSocketClient(config)

    @pytest.mark.asyncio
    async def test_get_shot_notes_success(self, client):
        """Test successful retrieval of shot notes."""
        mock_notes = {
            "rating": 4,
            "notes": "Great shot, well balanced",
            "balanceTaste": "balanced",
            "grindSetting": "12",
            "doseIn": 18.0,
            "doseOut": 36.0
        }

        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"notes": mock_notes}

            result = await client.get_shot_notes("000100")

            assert result == mock_notes
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "req:history:notes:get"
            # ID should be normalized (no leading zeros)
            assert call_args[1]["id"] == "100"

    @pytest.mark.asyncio
    async def test_get_shot_notes_normalizes_id(self, client):
        """Test that shot ID is normalized to integer string."""
        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"notes": None}

            # Various input formats should all normalize to "100"
            await client.get_shot_notes("100")
            assert mock_send.call_args[1]["id"] == "100"

            await client.get_shot_notes("000100")
            assert mock_send.call_args[1]["id"] == "100"

            await client.get_shot_notes("0100")
            assert mock_send.call_args[1]["id"] == "100"

    @pytest.mark.asyncio
    async def test_get_shot_notes_empty(self, client):
        """Test handling of empty notes response."""
        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"notes": None}

            result = await client.get_shot_notes("100")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_shot_notes_invalid_id(self, client):
        """Test that invalid shot ID raises ValueError."""
        with pytest.raises(ValueError):
            await client.get_shot_notes("invalid")

        with pytest.raises(ValueError):
            await client.get_shot_notes("abc123")

    @pytest.mark.asyncio
    async def test_save_shot_notes_success(self, client):
        """Test successful saving of shot notes."""
        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"msg": "Notes saved successfully"}

            result = await client.save_shot_notes(
                shot_id="100",
                rating=4,
                notes="Excellent extraction",
                balance_taste="balanced",
                grind_setting="12",
                dose_in=18.0,
                dose_out=36.0
            )

            assert result["msg"] == "Notes saved successfully"
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "req:history:notes:save"
            assert call_args[1]["id"] == "100"
            notes_data = call_args[1]["notes"]
            assert notes_data["rating"] == 4
            assert notes_data["notes"] == "Excellent extraction"
            assert notes_data["balanceTaste"] == "balanced"
            assert notes_data["grindSetting"] == "12"
            assert notes_data["doseIn"] == 18.0
            assert notes_data["doseOut"] == 36.0

    @pytest.mark.asyncio
    async def test_save_shot_notes_partial_fields(self, client):
        """Test saving notes with only some fields provided."""
        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"msg": "Notes saved"}

            # Only provide rating and notes
            await client.save_shot_notes(
                shot_id="100",
                rating=3,
                notes="Slightly sour"
            )

            notes_data = mock_send.call_args[1]["notes"]
            assert notes_data == {
                "rating": 3,
                "notes": "Slightly sour"
            }
            # Other fields should not be present
            assert "balanceTaste" not in notes_data
            assert "grindSetting" not in notes_data
            assert "doseIn" not in notes_data
            assert "doseOut" not in notes_data

    @pytest.mark.asyncio
    async def test_save_shot_notes_rating_only(self, client):
        """Test saving only a rating without notes."""
        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"msg": "Notes saved"}

            await client.save_shot_notes(shot_id="100", rating=5)

            notes_data = mock_send.call_args[1]["notes"]
            assert notes_data == {"rating": 5}

    @pytest.mark.asyncio
    async def test_save_shot_notes_normalizes_id(self, client):
        """Test that shot ID is normalized when saving."""
        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"msg": "Notes saved"}

            await client.save_shot_notes(shot_id="000100", rating=4)

            assert mock_send.call_args[1]["id"] == "100"

    @pytest.mark.asyncio
    async def test_save_shot_notes_invalid_id(self, client):
        """Test that invalid shot ID raises ValueError."""
        with pytest.raises(ValueError):
            await client.save_shot_notes(shot_id="invalid", rating=4)

    @pytest.mark.asyncio
    async def test_save_shot_notes_zero_rating(self, client):
        """Test saving a zero rating (valid but edge case)."""
        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"msg": "Notes saved"}

            await client.save_shot_notes(shot_id="100", rating=0)

            notes_data = mock_send.call_args[1]["notes"]
            assert notes_data["rating"] == 0

    @pytest.mark.asyncio
    async def test_get_shot_notes_websocket_error(self, client):
        """Test handling of WebSocket errors during get."""
        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = GaggimateError(
                ErrorCode.WEBSOCKET_ERROR,
                "Connection failed"
            )

            with pytest.raises(GaggimateError) as exc_info:
                await client.get_shot_notes("100")

            assert exc_info.value.code == ErrorCode.WEBSOCKET_ERROR

    @pytest.mark.asyncio
    async def test_save_shot_notes_timeout(self, client):
        """Test handling of timeout during save."""
        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = GaggimateError(
                ErrorCode.TIMEOUT,
                "Request timed out"
            )

            with pytest.raises(GaggimateError) as exc_info:
                await client.save_shot_notes(shot_id="100", rating=4)

            assert exc_info.value.code == ErrorCode.TIMEOUT

    @pytest.mark.asyncio
    async def test_save_shot_notes_device_unreachable(self, client):
        """Test handling of unreachable device during save."""
        with patch.object(client, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = GaggimateError(
                ErrorCode.DEVICE_UNREACHABLE,
                "Cannot connect to device"
            )

            with pytest.raises(GaggimateError) as exc_info:
                await client.save_shot_notes(shot_id="100", rating=4)

            assert exc_info.value.code == ErrorCode.DEVICE_UNREACHABLE


class TestWebSocketClientUrl:
    """Tests for WebSocket URL construction."""

    def test_ws_url_default(self):
        """Test default WebSocket URL construction."""
        config = GaggimateConfig(gaggimate_host="gaggimate.local")
        client = GaggimateWebSocketClient(config)
        assert client.ws_url == "ws://gaggimate.local/ws"

    def test_ws_url_with_ip(self):
        """Test WebSocket URL with IP address."""
        config = GaggimateConfig(gaggimate_host="192.168.1.100")
        client = GaggimateWebSocketClient(config)
        assert client.ws_url == "ws://192.168.1.100/ws"

    def test_ws_url_with_https(self):
        """Test WebSocket URL with WSS protocol."""
        config = GaggimateConfig(gaggimate_host="gaggimate.local", gaggimate_protocol="wss")
        client = GaggimateWebSocketClient(config)
        assert client.ws_url == "wss://gaggimate.local/ws"
