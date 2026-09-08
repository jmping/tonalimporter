"""Sensors for Tonal Companion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class TonalSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]


SENSORS = (
    TonalSensorDescription(key="strength_overall", name="Strength Score", icon="mdi:arm-flex", value_fn=lambda d: d.get("summary", {}).get("strength", {}).get("overall")),
    TonalSensorDescription(key="strength_upper", name="Upper Strength Score", icon="mdi:arm-flex", value_fn=lambda d: d.get("summary", {}).get("strength", {}).get("upper")),
    TonalSensorDescription(key="strength_lower", name="Lower Strength Score", icon="mdi:weight-lifter", value_fn=lambda d: d.get("summary", {}).get("strength", {}).get("lower")),
    TonalSensorDescription(key="strength_core", name="Core Strength Score", icon="mdi:human", value_fn=lambda d: d.get("summary", {}).get("strength", {}).get("core")),
    TonalSensorDescription(key="workouts_7d", name="Workouts 7d", icon="mdi:calendar-week", value_fn=lambda d: d.get("summary", {}).get("rolling", {}).get("workouts_7d")),
    TonalSensorDescription(key="workouts_30d", name="Workouts 30d", icon="mdi:calendar-month", value_fn=lambda d: d.get("summary", {}).get("rolling", {}).get("workouts_30d")),
    TonalSensorDescription(key="volume_7d", name="Volume 7d", icon="mdi:weight-pound", native_unit_of_measurement="lb", value_fn=lambda d: d.get("summary", {}).get("rolling", {}).get("volume_7d")),
    TonalSensorDescription(key="volume_30d", name="Volume 30d", icon="mdi:weight-pound", native_unit_of_measurement="lb", value_fn=lambda d: d.get("summary", {}).get("rolling", {}).get("volume_30d")),
    TonalSensorDescription(key="total_workouts", name="Total Workouts", icon="mdi:counter", value_fn=lambda d: d.get("summary", {}).get("profile", {}).get("total_workouts")),
    TonalSensorDescription(key="latest_workout", name="Latest Workout", icon="mdi:dumbbell", value_fn=lambda d: d.get("summary", {}).get("latest_workout", {}).get("title")),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(TonalSensor(coordinator, entry, description) for description in SENSORS)


class TonalSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry: ConfigEntry, description: TonalSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Tonal",
            manufacturer="Tonal",
            model="Companion data service",
        )

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self):
        if self.entity_description.key != "latest_workout":
            return None
        return (self.coordinator.data or {}).get("summary", {}).get("latest_workout", {})
