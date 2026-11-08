"""Tests for the Transmission number platform."""

from unittest.mock import AsyncMock, patch

from syrupy.assertion import SnapshotAssertion
from transmission_rpc.session import Session

from homeassistant.components.number import (
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
)
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import setup_integration

from tests.common import MockConfigEntry, snapshot_platform

DOWNLOAD_SPEED_LIMIT_ENTITY_ID = "number.transmission_download_speed_limit"


async def test_numbers(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    mock_transmission_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the number entities."""
    with patch("homeassistant.components.transmission.PLATFORMS", [Platform.NUMBER]):
        await setup_integration(hass, mock_config_entry)

    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


async def test_set_download_speed_limit(
    hass: HomeAssistant,
    mock_transmission_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test setting the download speed limit writes it to Transmission."""
    client = mock_transmission_client.return_value

    session_fields = {"download-dir": "/downloads", "speed-limit-down": 100}

    def set_session_side_effect(**kwargs: int) -> None:
        if "speed_limit_down" in kwargs:
            session_fields["speed-limit-down"] = kwargs["speed_limit_down"]

    client.set_session.side_effect = set_session_side_effect
    client.get_session.side_effect = lambda: Session(fields=session_fields)

    await setup_integration(hass, mock_config_entry)

    state = hass.states.get(DOWNLOAD_SPEED_LIMIT_ENTITY_ID)
    assert state is not None
    assert state.state == "100"

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: DOWNLOAD_SPEED_LIMIT_ENTITY_ID, ATTR_VALUE: 500},
        blocking=True,
    )

    client.set_session.assert_called_once_with(speed_limit_down=500)

    state = hass.states.get(DOWNLOAD_SPEED_LIMIT_ENTITY_ID)
    assert state is not None
    assert state.state == "500"
