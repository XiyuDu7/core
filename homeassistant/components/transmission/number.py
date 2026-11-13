"""Support for setting Transmission speed limits."""

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import override

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import EntityCategory, UnitOfDataRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import TransmissionConfigEntry, TransmissionDataUpdateCoordinator
from .entity import TransmissionEntity

PARALLEL_UPDATES = 0
MAX_SPEED_LIMIT = 1_000_000


@dataclass(frozen=True, kw_only=True)
class TransmissionNumberEntityDescription(NumberEntityDescription):
    """Entity description class for Transmission numbers."""

    value_func: Callable[[TransmissionDataUpdateCoordinator], float | None]
    set_func: Callable[[TransmissionDataUpdateCoordinator, float], None]


NUMBER_TYPES: tuple[TransmissionNumberEntityDescription, ...] = (
    TransmissionNumberEntityDescription(
        key="download_speed_limit",
        translation_key="download_speed_limit",
        device_class=NumberDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.KILOBYTES_PER_SECOND,
        entity_category=EntityCategory.CONFIG,
        mode=NumberMode.BOX,
        native_min_value=0,
        native_max_value=MAX_SPEED_LIMIT,
        native_step=1,
        value_func=lambda coordinator: coordinator.get_download_speed_limit(),
        set_func=lambda coordinator, value: coordinator.set_download_speed_limit(
            int(value)
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: TransmissionConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Transmission number entities."""

    coordinator = config_entry.runtime_data

    async_add_entities(
        TransmissionNumber(coordinator, description) for description in NUMBER_TYPES
    )


class TransmissionNumber(TransmissionEntity, NumberEntity):
    """Representation of a Transmission number."""

    entity_description: TransmissionNumberEntityDescription

    @property
    @override
    def native_value(self) -> float | None:
        """Return the current value."""
        return self.entity_description.value_func(self.coordinator)

    @override
    async def async_set_native_value(self, value: float) -> None:
        """Set a new value."""
        await self._async_write_and_refresh(
            partial(self.entity_description.set_func, self.coordinator, value)
        )
