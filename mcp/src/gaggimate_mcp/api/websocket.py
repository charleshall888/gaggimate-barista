"""WebSocket client for Gaggimate API.

Handles profile operations via WebSocket protocol:
- List profiles: req:profiles:list
- Load profile: req:profiles:load
- Save profile: req:profiles:save
"""

import asyncio
import json
import time
import random
from typing import Optional, Any
from websockets import connect
from websockets.exceptions import WebSocketException

from gaggimate_mcp.config import GaggimateConfig
from gaggimate_mcp.errors import GaggimateError, ErrorCode
from gaggimate_mcp.logging_config import get_logger

logger = get_logger(__name__)


def generate_request_id() -> str:
    """Generate unique request ID."""
    timestamp = int(time.time() * 1000)
    random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=9))
    return f"mcp-{timestamp}-{random_suffix}"


class GaggimateWebSocketClient:
    """WebSocket client for Gaggimate API."""

    def __init__(self, config: Optional[GaggimateConfig] = None):
        """Initialize WebSocket client.

        Args:
            config: Configuration object (uses default if None)
        """
        self.config = config or GaggimateConfig()
        self.timeout = 5.0  # 5 second timeout

    @property
    def ws_url(self) -> str:
        """Get WebSocket URL from config."""
        protocol = "wss" if self.config.use_https else "ws"
        return f"{protocol}://{self.config.host}/ws"

    async def _send_request(
        self,
        request_type: str,
        request_id: str,
        **kwargs: Any
    ) -> dict:
        """Send WebSocket request and wait for response.

        Args:
            request_type: Request type (e.g., 'req:profiles:list')
            request_id: Unique request ID
            **kwargs: Additional request parameters

        Returns:
            Response dictionary

        Raises:
            GaggimateError: If connection fails or request times out
        """
        try:
            async with connect(self.ws_url) as websocket:
                # Send request
                request = {
                    "tp": request_type,
                    "rid": request_id,
                    **kwargs
                }
                await websocket.send(json.dumps(request))
                logger.debug("ws_request_sent", request_type=request_type, request_id=request_id)

                # Wait for matching response
                response_type = request_type.replace("req:", "res:")
                timeout_at = time.time() + self.timeout

                while time.time() < timeout_at:
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=self.timeout
                        )

                        response = json.loads(message)

                        # Check if this is our response
                        if response.get("tp") == response_type and response.get("rid") == request_id:
                            if response.get("error"):
                                logger.error(
                                    "ws_api_error",
                                    request_type=request_type,
                                    error=response["error"]
                                )
                                raise GaggimateError(
                                    code=ErrorCode.API_ERROR,
                                    message=f"Gaggimate API error: {response['error']}"
                                )

                            logger.debug("ws_response_received", request_type=request_type)
                            return response

                        # Ignore other messages (like evt:status)
                        logger.debug("ws_message_ignored", message_type=response.get("tp"))

                    except asyncio.TimeoutError:
                        logger.error("ws_timeout", request_type=request_type, url=self.ws_url)
                        raise GaggimateError(
                            code=ErrorCode.TIMEOUT,
                            message=f"Request timeout: No response from {self.ws_url}"
                        )

                # If we exit the loop, timeout occurred
                raise GaggimateError(
                    code=ErrorCode.TIMEOUT,
                    message=f"Request timeout: No matching response for {request_id}"
                )

        except WebSocketException as e:
            logger.error("ws_connection_error", error=str(e), url=self.ws_url)
            raise GaggimateError(
                code=ErrorCode.WEBSOCKET_ERROR,
                message=f"WebSocket error: {str(e)}"
            ) from e
        except json.JSONDecodeError as e:
            logger.error("ws_json_error", error=str(e))
            raise GaggimateError(
                code=ErrorCode.PARSE_ERROR,
                message=f"Failed to parse WebSocket response: {str(e)}"
            ) from e

    async def list_profiles(self) -> list[dict]:
        """List all available profiles.

        Returns:
            List of profile dictionaries

        Raises:
            GaggimateError: If request fails
        """
        request_id = generate_request_id()
        logger.info("listing_profiles", url=self.ws_url)

        response = await self._send_request("req:profiles:list", request_id)
        profiles = response.get("profiles", [])

        logger.info("profiles_listed", count=len(profiles))
        return profiles

    async def load_profile(self, profile_id: str) -> Optional[dict]:
        """Load a specific profile by ID.

        Args:
            profile_id: Profile identifier

        Returns:
            Profile dictionary, or None if not found

        Raises:
            GaggimateError: If request fails
        """
        request_id = generate_request_id()
        logger.info("loading_profile", profile_id=profile_id, url=self.ws_url)

        response = await self._send_request(
            "req:profiles:load",
            request_id,
            id=profile_id
        )
        profile = response.get("profile")

        if profile:
            logger.info("profile_loaded", profile_id=profile_id)
        else:
            logger.warning("profile_not_found", profile_id=profile_id)

        return profile

    async def save_profile(self, profile: dict) -> dict:
        """Save or update a profile.

        Args:
            profile: Complete profile dictionary

        Returns:
            Saved profile dictionary

        Raises:
            GaggimateError: If request fails
        """
        request_id = generate_request_id()
        profile_id = profile.get("id", "new")
        logger.info("saving_profile", profile_id=profile_id, url=self.ws_url)

        response = await self._send_request(
            "req:profiles:save",
            request_id,
            profile=profile
        )
        saved_profile = response.get("profile", profile)

        logger.info("profile_saved", profile_id=saved_profile.get("id", profile_id))
        return saved_profile

    async def delete_profile(self, profile_id: str) -> dict:
        """Delete a profile by ID.

        Args:
            profile_id: Profile identifier to delete

        Returns:
            Response dictionary with deletion result

        Raises:
            GaggimateError: If request fails
        """
        request_id = generate_request_id()
        logger.info("deleting_profile", profile_id=profile_id, url=self.ws_url)

        response = await self._send_request(
            "req:profiles:delete",
            request_id,
            id=profile_id
        )

        logger.info("profile_deleted", profile_id=profile_id)
        return response

    async def create_or_update_profile(
        self,
        label: str,
        temperature: float,
        phases: list[dict],
        profile_id: Optional[str] = None,
        profile_type: str = "pro"
    ) -> dict:
        """Create or update a profile with simplified parameters.

        Args:
            label: Profile label/name
            temperature: Global temperature in Celsius
            phases: List of phase dictionaries
            profile_id: Existing profile ID (None to create new)
            profile_type: Profile type ('simple' or 'pro'), defaults to 'pro'

        Returns:
            Saved profile dictionary

        Raises:
            GaggimateError: If request fails
        """
        # Ensure AI suffix is present for agent-edited profiles
        ai_suffix = self.config.ai_profile_suffix
        if not label.endswith(ai_suffix):
            label = f"{label}{ai_suffix}"
        # Build complete profile object
        profile = {
            "label": label,
            "type": profile_type,
            "description": f"Profile: {label}",
            "temperature": temperature,
            "favorite": False,
            "selected": False,
            "utility": False,
            "phases": [
                {
                    "name": phase.get("name", "Phase"),
                    "phase": phase.get("phase", "brew"),
                    "valve": phase.get("valve", 1),  # Use agent's value, default to 1
                    "duration": phase["duration"],
                    "temperature": phase.get("temperature", temperature),
                    "transition": phase.get("transition", {
                        "type": "linear",
                        "duration": min(phase["duration"], 2),
                        "adaptive": True,
                    }),
                    "pump": phase.get("pump", {
                        "target": "pressure",
                        "pressure": 9,
                        "flow": 0,
                    }),
                    "targets": phase.get("targets", []),
                }
                for phase in phases
            ],
        }

        if profile_id:
            profile["id"] = profile_id

        return await self.save_profile(profile)

    async def find_profile_by_label(self, label: str) -> Optional[dict]:
        """Find a profile by its label.

        Args:
            label: Profile label to search for

        Returns:
            Profile dictionary if found, None otherwise

        Raises:
            GaggimateError: If request fails
        """
        profiles = await self.list_profiles()
        for profile in profiles:
            if profile.get("label") == label:
                return profile
        return None

    async def get_shot_notes(self, shot_id: str) -> Optional[dict]:
        """Get notes for a specific shot from the device.

        Args:
            shot_id: Shot identifier (should be integer string without leading zeros)

        Returns:
            Notes dictionary, or None if no notes exist

        Raises:
            GaggimateError: If request fails
        """
        # Normalize shot ID - API expects integer string without leading zeros
        normalized_id = str(int(shot_id))
        request_id = generate_request_id()
        logger.info("getting_shot_notes", shot_id=normalized_id, url=self.ws_url)

        response = await self._send_request(
            "req:history:notes:get",
            request_id,
            id=normalized_id
        )
        notes = response.get("notes")

        if notes:
            logger.info("shot_notes_retrieved", shot_id=normalized_id)
        else:
            logger.debug("shot_notes_empty", shot_id=normalized_id)

        return notes

    async def save_shot_notes(
        self,
        shot_id: str,
        rating: Optional[int] = None,
        notes: Optional[str] = None,
        balance_taste: Optional[str] = None,
        grind_setting: Optional[str] = None,
        dose_in: Optional[float] = None,
        dose_out: Optional[float] = None,
        bean_type: Optional[str] = None,
    ) -> dict:
        """Save notes for a specific shot to the device.

        Implements read-modify-write semantics against the firmware 1.8.0
        native sidecar schema. Firmware truncate-writes the sidecar on save,
        so any existing fields not present in the payload would be silently
        clobbered. We read the existing sidecar first, overlay only the
        non-None caller fields (mapped to camelCase), stringify numeric
        fields that firmware reads with .is<String>() (doseIn/doseOut/ratio),
        preserve/synthesize the id field, and short-circuit if nothing
        actually changed.

        Args:
            shot_id: Shot identifier (will be normalized to integer string)
            rating: Star rating (0-5)
            notes: Tasting notes text
            balance_taste: Taste balance ("bitter", "balanced", "sour")
            grind_setting: Grinder setting used
            dose_in: Coffee dose in grams
            dose_out: Espresso output in grams
            bean_type: Bean/coffee identifier

        Returns:
            Response from the API (or synthetic no-op response if unchanged)

        Raises:
            GaggimateError: If request fails
        """
        # Normalize shot ID - API expects integer string without leading zeros
        normalized_id = str(int(shot_id))
        request_id = generate_request_id()
        logger.info("saving_shot_notes", shot_id=normalized_id, url=self.ws_url)

        # Read existing sidecar (RMW step 1). Treat None / non-dict / falsy
        # returns as "no existing notes" and start from an empty dict.
        existing_raw = await self.get_shot_notes(normalized_id)
        if isinstance(existing_raw, dict):
            existing: dict[str, Any] = existing_raw
        else:
            existing = {}

        # Spread existing state into the merged payload.
        merged_notes: dict[str, Any] = dict(existing)

        # Track whether the caller actually passed any field updates. Used
        # for the no-op short-circuit: if nothing was passed AND nothing
        # changed in the merge, skip the wire write entirely.
        caller_provided_any = False

        if rating is not None:
            merged_notes["rating"] = rating
            caller_provided_any = True
        if notes is not None:
            merged_notes["notes"] = notes
            caller_provided_any = True
        if balance_taste is not None:
            merged_notes["balanceTaste"] = balance_taste
            caller_provided_any = True
        if grind_setting is not None:
            merged_notes["grindSetting"] = grind_setting
            caller_provided_any = True
        if dose_in is not None:
            # Firmware reads doseIn as String (.is<String>()) - stringify
            merged_notes["doseIn"] = str(dose_in)
            caller_provided_any = True
        if dose_out is not None:
            # Firmware reads doseOut as String (.is<String>()) - stringify
            # to avoid the index-volume column being zeroed.
            merged_notes["doseOut"] = str(dose_out)
            caller_provided_any = True
        if bean_type is not None:
            merged_notes["beanType"] = bean_type
            caller_provided_any = True

        # Compute ratio when both doses are provided as truthy numerics.
        # If only one is provided, leave any pre-existing ratio untouched.
        if dose_in is not None and dose_out is not None:
            try:
                dose_in_f = float(dose_in)
                dose_out_f = float(dose_out)
                if dose_in_f != 0:
                    ratio_val = round(dose_out_f / dose_in_f, 3)
                    merged_notes["ratio"] = str(ratio_val)
            except (TypeError, ValueError):
                # Non-numeric input - skip ratio computation rather than crash
                pass

        # Preserve existing id if present, else synthesize from normalized_id
        # (unpadded integer string). The merged payload MUST carry an id key
        # because firmware uses it as the sidecar primary key.
        if "id" not in merged_notes:
            merged_notes["id"] = normalized_id

        # No-op short-circuit: if the merged payload is dict-equal to what
        # was already on the device, nothing changed regardless of whether
        # the caller passed same-value fields — skip the wire write. Return
        # a synthetic success response so callers (e.g. manage_shot_notes)
        # still observe device_synced=True.
        if merged_notes == existing:
            logger.debug(
                "rmw_merge_skipped_noop",
                shot_id=normalized_id,
                request_id=request_id,
            )
            return {"msg": "no-op: unchanged", "id": normalized_id}

        response = await self._send_request(
            "req:history:notes:save",
            request_id,
            id=normalized_id,
            notes=merged_notes,
        )

        logger.info("shot_notes_saved", shot_id=normalized_id, msg=response.get("msg"))
        return response
