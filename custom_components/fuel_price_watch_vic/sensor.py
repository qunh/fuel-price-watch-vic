from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, FUEL_TYPES
from .coordinator import FuelPriceCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one price sensor + station/address sensors per fuel type per person."""
    coordinators: dict = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for coordinator in coordinators.values():
        for fuel_type in FUEL_TYPES:
            entities.append(FuelPriceSensor(coordinator, entry, fuel_type))
            entities.append(
                FuelFieldSensor(
                    coordinator, entry, fuel_type,
                    field_key="station_name",
                    field_label="Station",
                    icon="mdi:store",
                )
            )
            entities.append(
                FuelFieldSensor(
                    coordinator, entry, fuel_type,
                    field_key="address",
                    field_label="Address",
                    icon="mdi:map-marker",
                )
            )
    async_add_entities(entities)


class FuelPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the cheapest available price for one fuel type within radius."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "c/L"
    _attr_icon = "mdi:gas-station"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FuelPriceCoordinator,
        entry: ConfigEntry,
        fuel_type: str,
    ) -> None:
        super().__init__(coordinator)
        self._fuel_type = fuel_type
        self._attr_unique_id = f"{entry.entry_id}_{coordinator.person_entity_id}_{fuel_type}"
        self._attr_name = FUEL_TYPES.get(fuel_type, fuel_type)
        self._attr_extra_state_attributes: dict = {}
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, f"{coordinator.entry.entry_id}_{coordinator.person_entity_id}")
            },
            name=f"Fuel Price Watch VIC \u2014 {coordinator.person_name}",
            manufacturer="Service Victoria",
            model="Fair Fuel Open Data",
        )
        self._update_from_coordinator()

    def _update_from_coordinator(self) -> None:
        """Sync native_value and extra_state_attributes from coordinator data."""
        data = self.coordinator.data or {}
        d = data.get(self._fuel_type)
        if d:
            self._attr_native_value = d.get("price")
            lat = d.get("station_lat")
            lon = d.get("station_lon")
            attrs: dict = {
                "fuel_type": self._fuel_type,
                "station_name": d.get("station_name", ""),
                "address": d.get("address", ""),
                "phone": d.get("phone", ""),
                "distance_m": d.get("distance_m"),
                "updated_at": d.get("updated_at", ""),
            }
            if lat is not None and lon is not None:
                attrs["directions_url"] = (
                    f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
                )
            self._attr_extra_state_attributes = attrs
        else:
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_from_coordinator()
        self.async_write_ha_state()


class FuelFieldSensor(CoordinatorEntity, SensorEntity):
    """Text sensor exposing a single field (station name, address) for one fuel type."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FuelPriceCoordinator,
        entry: ConfigEntry,
        fuel_type: str,
        field_key: str,
        field_label: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator)
        self._fuel_type = fuel_type
        self._field_key = field_key
        self._attr_unique_id = (
            f"{entry.entry_id}_{coordinator.person_entity_id}_{fuel_type}_{field_key}"
        )
        self._attr_name = f"{FUEL_TYPES.get(fuel_type, fuel_type)} {field_label}"
        self._attr_icon = icon
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, f"{coordinator.entry.entry_id}_{coordinator.person_entity_id}")
            },
            name=f"Fuel Price Watch VIC \u2014 {coordinator.person_name}",
            manufacturer="Service Victoria",
            model="Fair Fuel Open Data",
        )
        self._update_from_coordinator()

    def _update_from_coordinator(self) -> None:
        data = self.coordinator.data or {}
        d = data.get(self._fuel_type)
        self._attr_native_value = d.get(self._field_key, "") if d else None

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_from_coordinator()
        self.async_write_ha_state()
