from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_FUEL_TYPE, CONF_SUBURB
from .coordinator import FuelPriceCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fuel Price sensor from a config entry."""
    coordinator: FuelPriceCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FuelPriceSensor(coordinator, entry)])


class FuelPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing the cheapest fuel price in an area."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "AUD/L"
    _attr_icon = "mdi:gas-station"

    def __init__(self, coordinator: FuelPriceCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_fuel_price"
        self._attr_name = (
            f"{entry.data[CONF_SUBURB]} {entry.data[CONF_FUEL_TYPE]} Price"
        )

    @property
    def native_value(self):
        """Return the cheapest price."""
        if self.coordinator.data:
            prices = self.coordinator.data.get("prices", [])
            if prices:
                return min(p["price"] for p in prices)
        return None

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}
        prices = self.coordinator.data.get("prices", [])
        if not prices:
            return {}
        cheapest = min(prices, key=lambda p: p["price"])
        return {
            "cheapest_station": cheapest.get("station_name"),
            "address": cheapest.get("address"),
            "suburb": self._entry.data[CONF_SUBURB],
            "fuel_type": self._entry.data[CONF_FUEL_TYPE],
            "last_updated": self.coordinator.last_updated,
        }

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": f"Fuel Price Watch - {self._entry.data[CONF_SUBURB]}",
            "manufacturer": "Fuel Price Watch VIC",
            "model": self._entry.data[CONF_FUEL_TYPE],
        }
