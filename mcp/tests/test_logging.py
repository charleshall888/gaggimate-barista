"""Tests for structured logging configuration."""

import pytest
import structlog
from gaggimate_mcp.logging_config import setup_logging, get_logger


class TestLoggingSetup:
    """Test logging configuration."""

    def test_setup_logging_info_level(self):
        """Test logging setup with INFO level."""
        setup_logging(log_level="INFO")
        logger = structlog.get_logger()
        assert logger is not None

    def test_setup_logging_debug_level(self):
        """Test logging setup with DEBUG level."""
        setup_logging(log_level="DEBUG")
        logger = structlog.get_logger()
        assert logger is not None

    def test_get_logger(self):
        """Test getting a logger instance."""
        setup_logging()
        logger = get_logger("test_module")
        assert logger is not None

    def test_logger_can_log(self, capfd):
        """Test logger can write messages."""
        setup_logging(log_level="INFO")
        logger = get_logger("test")

        logger.info("test_message", key="value")

        # Capture stderr (structlog writes to stderr by default for MCP)
        captured = capfd.readouterr()
        # Check that something was logged (exact format depends on configuration)
        assert len(captured.err) > 0 or len(captured.out) > 0
