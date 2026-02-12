"""Tests for connection diagnostics module."""

import pytest
from unittest.mock import AsyncMock, patch
from gaggimate_mcp.diagnostics import ping_host, check_port, check_http_endpoint, diagnose_connection
from gaggimate_mcp.config import GaggimateConfig


@pytest.mark.asyncio
async def test_ping_host_success():
    """Test successful ping."""
    with patch('asyncio.create_subprocess_exec') as mock_exec:
        # Mock successful ping
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(
            b"PING gaggimate.local (192.168.1.100): 56 data bytes\n"
            b"64 bytes from 192.168.1.100: icmp_seq=0 ttl=64 time=10.5 ms\n"
            b"--- gaggimate.local ping statistics ---\n"
            b"3 packets transmitted, 3 packets received, 0.0% packet loss\n"
            b"round-trip min/avg/max/stddev = 10.5/15.2/20.1/4.2 ms\n",
            b""
        ))
        mock_exec.return_value = mock_proc

        result = await ping_host("gaggimate.local")

        assert result["reachable"] is True
        assert result["avg_time_ms"] == 15.2
        assert result["error"] is None


@pytest.mark.asyncio
async def test_ping_host_failure():
    """Test failed ping."""
    with patch('asyncio.create_subprocess_exec') as mock_exec:
        # Mock failed ping
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(
            b"",
            b"ping: cannot resolve gaggimate.local: Unknown host"
        ))
        mock_exec.return_value = mock_proc

        result = await ping_host("gaggimate.local")

        assert result["reachable"] is False
        assert result["avg_time_ms"] is None
        assert "cannot resolve" in result["error"]


@pytest.mark.asyncio
async def test_diagnose_connection_healthy():
    """Test full diagnostics with healthy connection."""
    config = GaggimateConfig(host="gaggimate.local", use_https=False)

    with patch('gaggimate_mcp.diagnostics.ping_host') as mock_ping, \
         patch('gaggimate_mcp.diagnostics.check_port') as mock_port, \
         patch('gaggimate_mcp.diagnostics.check_http_endpoint') as mock_http:

        # Mock all checks successful
        mock_ping.return_value = {
            "reachable": True,
            "avg_time_ms": 15.0,
            "error": None
        }
        mock_port.return_value = {
            "open": True,
            "error": None
        }
        mock_http.return_value = {
            "accessible": True,
            "status": 200,
            "error": None
        }

        result = await diagnose_connection(config)

        assert result["overall_status"] == "healthy"
        assert result["host"] == "gaggimate.local"
        assert len(result["issues"]) == 0
        assert "tests" in result
        assert result["tests"]["ping"]["reachable"] is True


@pytest.mark.asyncio
async def test_diagnose_connection_unreachable():
    """Test diagnostics with unreachable device."""
    config = GaggimateConfig(host="gaggimate.local")

    with patch('gaggimate_mcp.diagnostics.ping_host') as mock_ping:
        # Mock ping failure
        mock_ping.return_value = {
            "reachable": False,
            "avg_time_ms": None,
            "error": "Host unreachable"
        }

        result = await diagnose_connection(config)

        assert result["overall_status"] == "unreachable"
        assert len(result["issues"]) > 0
        assert any("unreachable" in issue.lower() for issue in result["issues"])
        assert len(result["recommendations"]) > 0


@pytest.mark.asyncio
async def test_diagnose_connection_high_latency():
    """Test diagnostics with high latency."""
    config = GaggimateConfig(host="gaggimate.local", use_https=False)

    with patch('gaggimate_mcp.diagnostics.ping_host') as mock_ping, \
         patch('gaggimate_mcp.diagnostics.check_port') as mock_port, \
         patch('gaggimate_mcp.diagnostics.check_http_endpoint') as mock_http:

        # Mock high latency but working connection
        mock_ping.return_value = {
            "reachable": True,
            "avg_time_ms": 150.0,  # High latency
            "error": None
        }
        mock_port.return_value = {
            "open": True,
            "error": None
        }
        mock_http.return_value = {
            "accessible": True,
            "status": 200,
            "error": None
        }

        result = await diagnose_connection(config)

        assert result["overall_status"] == "connected_with_warnings"
        assert any("latency" in issue.lower() for issue in result["issues"])
        assert any("wifi" in rec.lower() or "signal" in rec.lower()
                  for rec in result["recommendations"])


@pytest.mark.asyncio
async def test_diagnose_connection_https_misconfigured():
    """Test diagnostics detecting HTTPS misconfiguration."""
    config = GaggimateConfig(gaggimate_host="gaggimate.local", gaggimate_protocol="wss")

    with patch('gaggimate_mcp.diagnostics.ping_host') as mock_ping, \
         patch('gaggimate_mcp.diagnostics.check_port') as mock_port, \
         patch('gaggimate_mcp.diagnostics.check_http_endpoint') as mock_http:

        # Mock: device reachable, HTTP works, HTTPS doesn't
        mock_ping.return_value = {
            "reachable": True,
            "avg_time_ms": 15.0,
            "error": None
        }
        mock_port.return_value = {
            "open": True,
            "error": None
        }

        def http_side_effect(url, **kwargs):
            if url.startswith("https://"):
                return {
                    "accessible": False,
                    "status": None,
                    "error": "Connection refused"
                }
            else:
                return {
                    "accessible": True,
                    "status": 200,
                    "error": None
                }

        mock_http.side_effect = http_side_effect

        result = await diagnose_connection(config)

        assert any("https" in issue.lower() for issue in result["issues"])
        assert any("use_https" in rec.lower() for rec in result["recommendations"])
