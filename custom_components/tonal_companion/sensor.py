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
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None


def _summary(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("summary", {})


def _latest(data: dict[str, Any]) -> dict[str, Any]:
    return _summary(data).get("latest_workout", {})


def _strength(data: dict[str, Any]) -> dict[str, Any]:
    return _summary(data).get("strength", {})


def _profile(data: dict[str, Any]) -> dict[str, Any]:
    return _summary(data).get("profile", {})


def _records(data: dict[str, Any]) -> dict[str, Any]:
    return _summary(data).get("records", {})


def _window(data: dict[str, Any], days: int) -> dict[str, Any]:
    return _summary(data).get("rolling", {}).get("windows", {}).get(str(days), {})


SENSORS = (
    # Core entities enabled by default.
    TonalSensorDescription(key="strength_overall", name="Strength Score", icon="mdi:arm-flex", value_fn=lambda d: _strength(d).get("overall")),
    TonalSensorDescription(key="strength_upper", name="Upper Strength Score", icon="mdi:arm-flex", value_fn=lambda d: _strength(d).get("upper")),
    TonalSensorDescription(key="strength_lower", name="Lower Strength Score", icon="mdi:weight-lifter", value_fn=lambda d: _strength(d).get("lower")),
    TonalSensorDescription(key="strength_core", name="Core Strength Score", icon="mdi:human", value_fn=lambda d: _strength(d).get("core")),
    TonalSensorDescription(key="workouts_7d", name="Workouts 7d", icon="mdi:calendar-week", value_fn=lambda d: _window(d, 7).get("workouts")),
    TonalSensorDescription(key="workouts_30d", name="Workouts 30d", icon="mdi:calendar-month", value_fn=lambda d: _window(d, 30).get("workouts")),
    TonalSensorDescription(key="volume_7d", name="Volume 7d", icon="mdi:weight-pound", native_unit_of_measurement="lb", value_fn=lambda d: _window(d, 7).get("volume")),
    TonalSensorDescription(key="volume_30d", name="Volume 30d", icon="mdi:weight-pound", native_unit_of_measurement="lb", value_fn=lambda d: _window(d, 30).get("volume")),
    TonalSensorDescription(key="total_workouts", name="Total Workouts", icon="mdi:counter", value_fn=lambda d: _profile(d).get("total_workouts")),
    TonalSensorDescription(
        key="latest_workout",
        name="Latest Workout",
        icon="mdi:dumbbell",
        value_fn=lambda d: _latest(d).get("title"),
        attributes_fn=lambda d: _latest(d),
    ),

    # Lifetime/profile metrics.
    TonalSensorDescription(key="lifetime_volume", name="Lifetime Volume", icon="mdi:weight-pound", native_unit_of_measurement="lb", entity_registry_enabled_default=False, value_fn=lambda d: _profile(d).get("total_volume")),
    TonalSensorDescription(key="lifetime_reps", name="Lifetime Reps", icon="mdi:counter", entity_registry_enabled_default=False, value_fn=lambda d: _profile(d).get("total_reps")),
    TonalSensorDescription(key="lifetime_sets", name="Lifetime Sets", icon="mdi:counter", entity_registry_enabled_default=False, value_fn=lambda d: _profile(d).get("total_sets")),
    TonalSensorDescription(key="days_since_last_workout", name="Days Since Last Workout", icon="mdi:calendar-range", native_unit_of_measurement="d", entity_registry_enabled_default=False, value_fn=lambda d: _profile(d).get("days_since_last_workout")),
    TonalSensorDescription(key="first_workout", name="First Workout", icon="mdi:calendar-start", entity_registry_enabled_default=False, value_fn=lambda d: _profile(d).get("first_workout")),

    # Latest workout metrics.
    TonalSensorDescription(key="latest_workout_volume", name="Latest Workout Volume", icon="mdi:weight-pound", native_unit_of_measurement="lb", entity_registry_enabled_default=False, value_fn=lambda d: _latest(d).get("total_volume")),
    TonalSensorDescription(key="latest_workout_reps", name="Latest Workout Reps", icon="mdi:counter", entity_registry_enabled_default=False, value_fn=lambda d: _latest(d).get("total_reps")),
    TonalSensorDescription(key="latest_workout_sets", name="Latest Workout Sets", icon="mdi:counter", entity_registry_enabled_default=False, value_fn=lambda d: _latest(d).get("set_count")),
    TonalSensorDescription(key="latest_workout_movements", name="Latest Workout Movements", icon="mdi:dumbbell", entity_registry_enabled_default=False, value_fn=lambda d: _latest(d).get("movement_count"), attributes_fn=lambda d: {"movements": _latest(d).get("movements", [])}),
    TonalSensorDescription(key="latest_workout_duration", name="Latest Workout Duration", icon="mdi:timer-outline", native_unit_of_measurement="s", entity_registry_enabled_default=False, value_fn=lambda d: _latest(d).get("duration")),
    TonalSensorDescription(key="latest_workout_time", name="Latest Workout Time", icon="mdi:calendar-clock", entity_registry_enabled_default=False, value_fn=lambda d: _latest(d).get("begin_time")),
    TonalSensorDescription(key="latest_workout_type", name="Latest Workout Type", icon="mdi:tag-outline", entity_registry_enabled_default=False, value_fn=lambda d: _latest(d).get("type")),
    TonalSensorDescription(key="latest_max_weight", name="Latest Workout Max Weight", icon="mdi:weight-pound", native_unit_of_measurement="lb", entity_registry_enabled_default=False, value_fn=lambda d: _latest(d).get("max_weight")),
    TonalSensorDescription(key="latest_max_one_rep_max", name="Latest Workout Max 1RM", icon="mdi:weight-lifter", native_unit_of_measurement="lb", entity_registry_enabled_default=False, value_fn=lambda d: _latest(d).get("max_one_rep_max")),
    TonalSensorDescription(key="latest_best_rom", name="Latest Workout Best ROM", icon="mdi:angle-acute", entity_registry_enabled_default=False, value_fn=lambda d: _latest(d).get("best_range_of_motion")),
    TonalSensorDescription(key="latest_max_power", name="Latest Workout Max Power", icon="mdi:flash", entity_registry_enabled_default=False, value_fn=lambda d: _latest(d).get("max_power")),

    # Additional rolling windows.
    TonalSensorDescription(key="workouts_14d", name="Workouts 14d", icon="mdi:calendar-range", entity_registry_enabled_default=False, value_fn=lambda d: _window(d, 14).get("workouts")),
    TonalSensorDescription(key="workouts_90d", name="Workouts 90d", icon="mdi:calendar-range", entity_registry_enabled_default=False, value_fn=lambda d: _window(d, 90).get("workouts")),
    TonalSensorDescription(key="workouts_365d", name="Workouts 365d", icon="mdi:calendar", entity_registry_enabled_default=False, value_fn=lambda d: _window(d, 365).get("workouts")),
    TonalSensorDescription(key="volume_14d", name="Volume 14d", icon="mdi:weight-pound", native_unit_of_measurement="lb", entity_registry_enabled_default=False, value_fn=lambda d: _window(d, 14).get("volume")),
    TonalSensorDescription(key="volume_90d", name="Volume 90d", icon="mdi:weight-pound", native_unit_of_measurement="lb", entity_registry_enabled_default=False, value_fn=lambda d: _window(d, 90).get("volume")),
    TonalSensorDescription(key="volume_365d", name="Volume 365d", icon="mdi:weight-pound", native_unit_of_measurement="lb", entity_registry_enabled_default=False, value_fn=lambda d: _window(d, 365).get("volume")),
    TonalSensorDescription(key="reps_7d", name="Reps 7d", icon="mdi:counter", entity_registry_enabled_default=False, value_fn=lambda d: _window(d, 7).get("reps")),
    TonalSensorDescription(key="reps_30d", name="Reps 30d", icon="mdi:counter", entity_registry_enabled_default=False, value_fn=lambda d: _window(d, 30).get("reps")),
    TonalSensorDescription(key="avg_volume_7d", name="Average Workout Volume 7d", icon="mdi:chart-line", native_unit_of_measurement="lb", entity_registry_enabled_default=False, value_fn=lambda d: _window(d, 7).get("avg_volume_per_workout")),
    TonalSensorDescription(key="avg_volume_30d", name="Average Workout Volume 30d", icon="mdi:chart-line", native_unit_of_measurement="lb", entity_registry_enabled_default=False, value_fn=lambda d: _window(d, 30).get("avg_volume_per_workout")),

    # Best-observed records from downloaded workout data.
    TonalSensorDescription(key="record_workout_volume", name="Record Workout Volume", icon="mdi:trophy", native_unit_of_measurement="lb", entity_registry_enabled_default=False, value_fn=lambda d: _records(d).get("max_workout_volume")),
    TonalSensorDescription(key="record_workout_reps", name="Record Workout Reps", icon="mdi:trophy", entity_registry_enabled_default=False, value_fn=lambda d: _records(d).get("max_workout_reps")),
    TonalSensorDescription(key="record_set_weight", name="Record Set Weight", icon="mdi:trophy", native_unit_of_measurement="lb", entity_registry_enabled_default=False, value_fn=lambda d: _records(d).get("max_set_weight")),
    TonalSensorDescription(key="record_one_rep_max", name="Record 1RM", icon="mdi:trophy", native_unit_of_measurement="lb", entity_registry_enabled_default=False, value_fn=lambda d: _records(d).get("max_one_rep_max")),
    TonalSensorDescription(key="record_rom", name="Best Range of Motion", icon="mdi:trophy", entity_registry_enabled_default=False, value_fn=lambda d: _records(d).get("best_range_of_motion")),
    TonalSensorDescription(key="record_power", name="Record Power", icon="mdi:flash", entity_registry_enabled_default=False, value_fn=lambda d: _records(d).get("max_power")),

    # Attribute-rich overview sensors.
    TonalSensorDescription(key="recent_workouts", name="Recent Workouts", icon="mdi:history", entity_registry_enabled_default=False, value_fn=lambda d: len(_summary(d).get("recent_workouts", [])), attributes_fn=lambda d: {"workouts": _summary(d).get("recent_workouts", [])}),
    TonalSensorDescription(key="workout_types", name="Workout Types", icon="mdi:chart-donut", entity_registry_enabled_default=False, value_fn=lambda d: len(_summary(d).get("workout_types", {})), attributes_fn=lambda d: _summary(d).get("workout_types", {})),
    TonalSensorDescription(key="strength_history", name="Strength Score History", icon="mdi:chart-line", entity_registry_enabled_default=False, value_fn=lambda d: len(_strength(d).get("history", [])), attributes_fn=lambda d: {"history": _strength(d).get("history", [])}),

    # Diagnostics.
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
        attributes_fn = getattr(self.entity_description, "attributes_fn", None)
        if attributes_fn is None:
            return None
        return attributes_fn(self.coordinator.data or {})
