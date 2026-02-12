"""Tests for structured error handling."""

import pytest
from gaggimate_mcp.errors import ErrorCode, GaggimateError


class TestErrorCode:
    """Test error code enumeration."""

    def test_error_code_values(self):
        """Test error code enum values exist."""
        assert ErrorCode.INVALID_INPUT
        assert ErrorCode.PROFILE_NOT_FOUND
        assert ErrorCode.SHOT_NOT_FOUND
        assert ErrorCode.UNAUTHORIZED
        assert ErrorCode.SAFETY_LIMIT_EXCEEDED
        assert ErrorCode.API_ERROR
        assert ErrorCode.PARSE_ERROR
        assert ErrorCode.TIMEOUT
        assert ErrorCode.DEVICE_UNREACHABLE
        assert ErrorCode.WEBSOCKET_ERROR

    def test_error_code_string_values(self):
        """Test error codes have correct string values."""
        assert ErrorCode.INVALID_INPUT.value == "invalid_input"
        assert ErrorCode.PROFILE_NOT_FOUND.value == "profile_not_found"
        assert ErrorCode.SHOT_NOT_FOUND.value == "shot_not_found"
        assert ErrorCode.UNAUTHORIZED.value == "unauthorized"
        assert ErrorCode.SAFETY_LIMIT_EXCEEDED.value == "safety_limit_exceeded"


class TestGaggimateError:
    """Test GaggimateError exception class."""

    def test_error_creation_minimal(self):
        """Test creating error with minimal fields."""
        error = GaggimateError(
            code=ErrorCode.INVALID_INPUT,
            message="Invalid temperature value"
        )
        assert error.code == ErrorCode.INVALID_INPUT
        assert error.message == "Invalid temperature value"
        assert error.details is None
        assert error.retryable is False

    def test_error_creation_with_details(self):
        """Test creating error with details."""
        error = GaggimateError(
            code=ErrorCode.SAFETY_LIMIT_EXCEEDED,
            message="Temperature exceeds safety limit",
            details={"temperature": 100, "max_allowed": 96}
        )
        assert error.code == ErrorCode.SAFETY_LIMIT_EXCEEDED
        assert error.message == "Temperature exceeds safety limit"
        assert error.details == {"temperature": 100, "max_allowed": 96}

    def test_error_creation_retryable(self):
        """Test creating retryable error."""
        error = GaggimateError(
            code=ErrorCode.TIMEOUT,
            message="Request timed out",
            retryable=True
        )
        assert error.retryable is True

    def test_error_to_dict(self):
        """Test error serialization to dict."""
        error = GaggimateError(
            code=ErrorCode.DEVICE_UNREACHABLE,
            message="Cannot connect to Gaggimate device",
            details={"host": "gaggimate.local"},
            retryable=True
        )
        result = error.to_dict()

        assert "error" in result
        assert result["error"]["code"] == "device_unreachable"
        assert result["error"]["message"] == "Cannot connect to Gaggimate device"
        assert result["error"]["details"] == {"host": "gaggimate.local"}
        assert result["error"]["retryable"] is True

    def test_error_to_dict_minimal(self):
        """Test error serialization with minimal fields."""
        error = GaggimateError(
            code=ErrorCode.PARSE_ERROR,
            message="Failed to parse shot data"
        )
        result = error.to_dict()

        assert result["error"]["code"] == "parse_error"
        assert result["error"]["message"] == "Failed to parse shot data"
        assert result["error"]["details"] == {}
        assert result["error"]["retryable"] is False

    def test_error_is_exception(self):
        """Test that GaggimateError is an Exception."""
        error = GaggimateError(
            code=ErrorCode.API_ERROR,
            message="API request failed"
        )
        assert isinstance(error, Exception)

    def test_error_can_be_raised(self):
        """Test that GaggimateError can be raised and caught."""
        with pytest.raises(GaggimateError) as exc_info:
            raise GaggimateError(
                code=ErrorCode.WEBSOCKET_ERROR,
                message="WebSocket connection failed"
            )

        assert exc_info.value.code == ErrorCode.WEBSOCKET_ERROR
        assert exc_info.value.message == "WebSocket connection failed"

    def test_error_str_representation(self):
        """Test error string representation."""
        error = GaggimateError(
            code=ErrorCode.INVALID_INPUT,
            message="Invalid input provided"
        )
        error_str = str(error)
        assert "invalid_input" in error_str
        assert "Invalid input provided" in error_str

    def test_client_error_codes(self):
        """Test client error codes (4xx equivalent)."""
        client_errors = [
            ErrorCode.INVALID_INPUT,
            ErrorCode.PROFILE_NOT_FOUND,
            ErrorCode.UNAUTHORIZED,
            ErrorCode.SAFETY_LIMIT_EXCEEDED,
        ]
        for code in client_errors:
            assert code.value  # Verify they exist

    def test_server_error_codes(self):
        """Test server error codes (5xx equivalent)."""
        server_errors = [
            ErrorCode.API_ERROR,
            ErrorCode.PARSE_ERROR,
            ErrorCode.TIMEOUT,
        ]
        for code in server_errors:
            assert code.value  # Verify they exist

    def test_external_error_codes(self):
        """Test external error codes."""
        external_errors = [
            ErrorCode.DEVICE_UNREACHABLE,
            ErrorCode.WEBSOCKET_ERROR,
        ]
        for code in external_errors:
            assert code.value  # Verify they exist
