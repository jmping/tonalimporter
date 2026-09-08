"""Sensors for ToneGet for Home Assistant."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class TonalSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]


def _summary(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("summary", {})


def _latest(data: dict[str, Any]) -> dict[str, Any]:
    return _summary(data).get("latest_workout", {})


def _strength(data: dict[str, Any]) -> dict[str, Any]:
    return _summary(data).get("strength", {})


SENSORS = (
    # Core entities enabled by default.
    TonalSensorDescription(key="strength_overall", name="Strength Score", icon="mdi:arm-flex", value_fn=lambda d: _strength(d).get("overall")),
    TonalSensorDescription(key="strength_upper", name="Upper Strength Score", icon="mdi:arm-flex", value_fn=lambda d: _strength(d).get("upper")),
    TonalSensorDescription(key="strength_lower", name="Lower Strength Score", icon="mdi:weight-lifter", value_fn=lambda d: _strength(d).get("lower")),
    TonalSensorDescription(key="strength_core", name="Core Strength Score", icon="mdi:human", value_fn=lambda d: _strength(d).get("core")),
    TonalSensorDescription(key="workouts_7d", name="Workouts 7d", icon="mdi:calendar-week", value_fn=lambda d: _summary(d).get("rolling", {}).get("workouts_7d")),
    TonalSensorDescription(key="workouts_30d", name="Workouts 30d", icon="mdi:calendar-month", value_fn=lambda d: _summary(d).get("rolling", {}).get("workouts_30d")),
    TonalSensorDescription(key="volume_7d", name="Volume 7d", icon="mdi:weight-pound", native_unit_of_measurement="lb", value_fn=lambda d: _summary(d).get("rolling", {}).get("volume_7d")),
    TonalSensorDescription(key="volume_30d", name="Volume 30d", icon="mdi:weight-pound", native_unit_of_measurement="lb", value_fn=lambda d: _summary(d).get("rolling", {}).get("volume_30d")),
    TonalSensorDescription(key="total_workouts", name="Total Workouts", icon="mdi:counter", value_fn=lambda d: _summary(d).get("profile", {}).get("total_workouts")),
    TonalSensorDescription(key="latest_workout", name="Latest Workout", icon="mdi:dumbbell", value_fn=lambda d: _latest(d).get("title")),

    # Richer entities are available but disabled by default to avoid clutter.
    TonalSensorDescription(key="lifetime_volume", name="Lifetime Volume", icon="mdi:weight-pound", native_unit_of_measurement="lb", entity_registry_enabled_default=False, value_fn=lambda d: _summary(d).get("profile", {}).get("total_volume")),
    TonalSensorDescription(key="latest_workout_volume", name="Latest Workout Volume", icon="mdi:weight-pound", native_unit_of_measurement="lb", entity_registry_enabled_default=False, value_fn=lambda d: _latest(d).get("total_volume")),
    TonalSensorDescription(key="latest_workout_reps", name="Latest Workout Reps", icon="mdi:counter", entity_registry_enabled_default=False, value_fn=lambda d: _latest(d).get("total_reps")),
    TonalSensorDescription(key="latest_workout_duration", name="Latest Workout Duration", icon="mdi:timer-outline", native_unit_of_measurement="s", entity_registry_enabled_default=False, value_fn=lambda d: _latest(d).get("duration")),
    TonalSensorDescription(key="latest_workout_time", name="Latest Workout Time", icon="mdi:calendar-clock", entity_registry_enabled_default=False, value_fn=lambda d: _latest(d).get("begin_time")),
    TonalSensorDescription(key="last_sync", name="Last Sync", icon="mdi:sync", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, value_fn=lambda d: d.get("last_sync")),
    TonalSensorDescription(key="service_status", name="Service Status", icon="mdi:heart-pulse", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False, value_fn=lambda d: d.get("status")),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    descriptions = list(SENSORS)

    # Create one optional sensor per region and muscle returned by ToneGet.
    snapshot = coordinator.data or {}
    regions = _strength(snapshot).get("regions", {})
    muscles = _strength(snapshot).get("muscles", {})

    for region_name in sorted(regions):
        key = f"region_{region_name.lower().replace(' ', '_')}"
        descriptions.append(
            TonalSensorDescription(
                key=key,
                name=f"{region_name} Strength Score",
                icon="mdi:arm-flex",
                entity_registry_enabled_default=False,
                value_fn=lambda d, name=region_name: _strength(d).get("regions", {}).get(name),
            )
        )

    for muscle_name in sorted(muscles):
        key = f"muscle_{muscle_name.lower().replace(' ', '_')}"
        descriptions.append(
            TonalSensorDescription(
                key=key,
                name=f"{muscle_name} Strength Score",
                icon="mdi:human-male-board",
                entity_registry_enabled_default=False,
                value_fn=lambda d, name=muscle_name: (_strength(d).get("muscles", {}).get(name) or {}).get("score"),
            )
        )

    async_add_entities(TonalSensor(coordinator, entry, description) for description in descriptions)


class TonalSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry: ConfigEntry, description: TonalSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="ToneGet for Home Assistant",
            manufacturer="Community integration (unofficial)",
            model="ToneGet-derived Tonal data bridge",
        )

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self):
        if self.entity_description.key != "latest_workout":
            return None
        return _latest(self.coordinator.data or {})
