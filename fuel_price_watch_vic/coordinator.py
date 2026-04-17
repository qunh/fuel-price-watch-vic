import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_FUEL_TYPE, CONF_POSTCODE, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

# Victorian Fuel Price API endpoint (FuelWatch-style)
FUEL_API_URL = "https://www.fuelwatch.vic.gov.au/api/prices"


class FuelPriceCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch fuel price data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        scan_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        """Fetch fuel price data from API."""
        postcode = self.entry.data[CONF_POSTCODE]
        fuel_type = self.entry.data[CONF_FUEL_TYPE]

        try:
            async with aiohttp.ClientSession() as session:
                params = {"postcode": postcode, "fuel_type": fuel_type}
                async with session.get(
                    FUEL_API_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error fetching fuel prices: {err}") from err
