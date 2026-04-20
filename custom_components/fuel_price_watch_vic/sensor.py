from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, FUEL_TYPES
from .coordinator import FuelPriceCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one sensor per fuel type per person found in coordinator data."""
    coordinators: dict = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for coordinator in coordinators.values():
        entities.extend(
            FuelPriceSensor(coordinator, entry, fuel_type)
            for fuel_type in coordinator.data
        )
    async_add_entities(entities)


class FuelPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the cheapest available price for one fuel type within radius."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "c/L"
    _attr_icon = "mdi:gas-station"

    def __init__(
        self,
        coordinator: FuelPriceCoordinator,
        entry: ConfigEntry,
        fuel_type: str,
    ) -> None:
        super().__init__(coordinator)
        self._fuel_type = fuel_type
        friendly = FUEL_TYPES.get(fuel_type, fuel_type)
        self._attr_unique_id = f"{entry.entry_id}_{coordinator.person_entity_id}_{fuel_type}"
        self._attr_name = friendly

    @property
    def _data(self) -> dict | None:
        if self.coordinator.data:
            return self.coordinator.data.get(self._fuel_type)
        return None

    @property
    def native_value(self) -> float | None:
        d = self._data
        return d["price"] if d else None

    @property
    def extra_state_attributes(self) -> dict:
        d = self._data
        if not d:
            return {}
        lat = d.get("station_lat")
        lon = d.get("station_lon")
        directions_url = (
            f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
            if lat is not None and lon is not None
            else None
        )
        attrs = {
            "fuel_type": self._fuel_type,
            "station_name": d["station_name"],
            "address": d["address"],
            "phone": d["phone"],
            "distance_m": d["distance_m"],
            "updated_at": d["updated_at"],
        }
        if directions_url:
            attrs["directions_url"] = directions_url
        return attrs

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {
                (DOMAIN, f"{self.coordinator.entry.entry_id}_{self.coordinator.person_entity_id}")
            },
            "name": f"Fuel Price Watch VIC — {self.coordinator.person_name}",
            "manufacturer": "Service Victoria",
            "model": "Fair Fuel Open Data",
        }
