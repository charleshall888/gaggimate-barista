"""HTTP client for Gaggimate API.

Handles shot history operations via HTTP:
- Fetch index.bin (shot history index)
- Fetch specific shot .slog files
"""

import asyncio
from typing import Optional

import aiohttp

from gaggimate_mcp.config import GaggimateConfig
from gaggimate_mcp.errors import GaggimateError, ErrorCode
from gaggimate_mcp.logging_config import get_logger
from gaggimate_mcp.parsers.index import parse_binary_index, index_to_shot_list
from gaggimate_mcp.parsers.shot import parse_binary_shot, ShotData

logger = get_logger(__name__)


class GaggimateHTTPClient:
    """HTTP client for Gaggimate API."""

    def __init__(self, config: Optional[GaggimateConfig] = None):
        """Initialize HTTP client.

        Args:
            config: Configuration object (uses default if None)
        """
        self.config = config or GaggimateConfig()
        # Per-attempt timeout comes from config (sized for the large .slog
        # shot-log download over a weak link), not a hardcoded 5s. Retries
        # cover transient blips. Total attempts = request_retries + 1.
        self.timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
        self.max_retries = self.config.request_retries
        self.retry_backoff = 0.5  # base seconds for exponential backoff

    @property
    def base_url(self) -> str:
        """Get base HTTP URL from config."""
        protocol = "https" if self.config.use_https else "http"
        return f"{protocol}://{self.config.host}/api/history"

    async def _get_bytes(self, url: str) -> tuple[int, bytes]:
        """GET ``url`` with retry/backoff on timeout and transient errors.

        Idempotent reads are retried up to ``self.max_retries`` times on
        ``asyncio.TimeoutError`` (the aiohttp total-timeout deadline) and
        ``aiohttp.ClientError`` (connection blips). Returns ``(status, body)``;
        ``body`` is empty for non-200 responses so the caller can branch on
        status (e.g. 404). After exhausting retries, raises a *classified*
        ``GaggimateError`` (``TIMEOUT`` or ``DEVICE_UNREACHABLE``) rather than
        letting a bare ``TimeoutError`` escape to the tool's catch-all.
        """
        last_exc: Optional[BaseException] = None
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(
                        url, headers={"Accept": "application/octet-stream"}
                    ) as response:
                        if response.status != 200:
                            return response.status, b""
                        return response.status, await response.read()
            except asyncio.TimeoutError as e:
                # aiohttp.ServerTimeoutError subclasses BOTH asyncio.TimeoutError
                # and ClientError, so this branch must precede ClientError.
                last_exc = e
                logger.warning(
                    "http_timeout_retry",
                    url=url,
                    attempt=attempt + 1,
                    max_attempts=self.max_retries + 1,
                    timeout_s=self.config.request_timeout,
                )
            except aiohttp.ClientError as e:
                last_exc = e
                logger.warning(
                    "http_connection_retry",
                    url=url,
                    attempt=attempt + 1,
                    max_attempts=self.max_retries + 1,
                    error=str(e),
                )
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_backoff * (2 ** attempt))

        attempts = self.max_retries + 1
        if isinstance(last_exc, asyncio.TimeoutError):
            raise GaggimateError(
                code=ErrorCode.TIMEOUT,
                message=(
                    f"Request timed out after {attempts} attempts "
                    f"({self.config.request_timeout}s each): {url}"
                ),
                retryable=True,
            ) from last_exc
        raise GaggimateError(
            code=ErrorCode.DEVICE_UNREACHABLE,
            message=f"HTTP connection error after {attempts} attempts: {last_exc}",
            retryable=True,
        ) from last_exc

    async def fetch_shot_index(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list[dict]:
        """Fetch shot history index.

        Args:
            limit: Maximum number of shots to return
            offset: Number of shots to skip

        Returns:
            List of shot metadata dictionaries (sorted newest first)

        Raises:
            GaggimateError: If request fails
        """
        url = f"{self.base_url}/index.bin"
        logger.info("fetching_shot_index", url=url)

        status, body = await self._get_bytes(url)
        if status == 404:
            # Index doesn't exist - empty history
            logger.info("shot_index_not_found", url=url)
            return []
        if status != 200:
            logger.error("http_error", status=status, url=url)
            raise GaggimateError(
                code=ErrorCode.API_ERROR,
                message=f"HTTP {status}"
            )

        try:
            index_data = parse_binary_index(body)
            shot_list = index_to_shot_list(index_data)
        except ValueError as e:
            logger.error("parse_error", error=str(e), url=url)
            raise GaggimateError(
                code=ErrorCode.PARSE_ERROR,
                message=f"Failed to parse index.bin: {str(e)}"
            ) from e

        # Apply offset and limit
        if offset and offset > 0:
            shot_list = shot_list[offset:]
        if limit and limit > 0:
            shot_list = shot_list[:limit]

        logger.info("shot_index_fetched", count=len(shot_list))
        return shot_list

    async def fetch_shot(self, shot_id: str) -> Optional[ShotData]:
        """Fetch a specific shot by ID.

        Args:
            shot_id: Shot identifier (will be zero-padded to 6 digits)

        Returns:
            Parsed shot data, or None if not found

        Raises:
            GaggimateError: If request fails (excluding 404)
        """
        # Normalize ID to 6 digits for both filename and storage
        padded_id = shot_id.zfill(6)
        url = f"{self.base_url}/{padded_id}.slog"
        logger.info("fetching_shot", shot_id=shot_id, padded_id=padded_id, url=url)

        status, body = await self._get_bytes(url)
        if status == 404:
            # Shot not found
            logger.warning("shot_not_found", shot_id=shot_id, url=url)
            return None
        if status != 200:
            logger.error("http_error", status=status, url=url)
            raise GaggimateError(
                code=ErrorCode.API_ERROR,
                message=f"HTTP {status}"
            )

        try:
            # Parse binary shot data - use padded_id as canonical ID
            shot_data = parse_binary_shot(body, padded_id)
        except ValueError as e:
            logger.error("parse_error", error=str(e), url=url)
            raise GaggimateError(
                code=ErrorCode.PARSE_ERROR,
                message=f"Failed to parse shot file: {str(e)}"
            ) from e

        logger.info("shot_fetched", shot_id=shot_id, samples=shot_data.sample_count)
        return shot_data

    async def list_recent_shots(self, limit: int = 10) -> list[dict]:
        """List recent shots (convenience method).

        Args:
            limit: Maximum number of shots to return (default 10)

        Returns:
            List of recent shot metadata dictionaries

        Raises:
            GaggimateError: If request fails
        """
        return await self.fetch_shot_index(limit=limit)
