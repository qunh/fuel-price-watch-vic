import logging
import math
import uuid
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_PRICES_ENDPOINT,
    CONF_CONSUMER_ID,
    CONF_LOCATION_SOURCE,
    CONF_RADIUS_KM,
    DEFAULT_LOCATION_SOURCE,
    DEFAULT_RADIUS_KM,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in metres between two lat/lon points."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class FuelPriceCoordinator(DataUpdateCoordinator):
    """Coordinator that fetches all VIC fuel prices and filters by radius."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        """Fetch prices from the Service Victoria API and return best per fuel type.

        Returns a dict keyed by fuel type code, e.g.:
          {
            "U91": {
              "price": 195.7,
              "station_name": "...",
              "address": "...",
              "phone": "...",
              "distance_m": 1234,
              "updated_at": "2024-01-01T00:00:00Z",
            },
            ...
          }
        """
        consumer_id: str = self.entry.data[CONF_CONSUMER_ID]
        radius_m: float = self.entry.options.get(
            CONF_RADIUS_KM, self.entry.data.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM)
        ) * 1000

        # Resolve coordinates from the configured location source
        location_source: str = self.entry.options.get(
            CONF_LOCATION_SOURCE,
            self.entry.data.get(CONF_LOCATION_SOURCE, DEFAULT_LOCATION_SOURCE),
        )
        location_state = self.hass.states.get(location_source)
        if location_state is None:
            raise UpdateFailed(
                f"Location source '{location_source}' not found. "
                "Check the integration options or ensure the device tracker is available."
            )
        try:
            home_lat: float = float(location_state.attributes["latitude"])
            home_lon: float = float(location_state.attributes["longitude"])
        except (KeyError, TypeError, ValueError) as err:
            raise UpdateFailed(
                f"'{location_source}' has no latitude/longitude attributes. "
                "If using a device tracker, ensure location permission is granted in the HA app."
            ) from err

        headers = {
            "x-consumer-id": consumer_id,
            "x-transactionid": str(uuid.uuid4()),
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    API_PRICES_ENDPOINT,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status in (401, 403):
                        raise UpdateFailed(
                            f"API authentication failed (HTTP {resp.status}). "
                            "Check your consumer ID."
                        )
                    resp.raise_for_status()
                    raw = await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error contacting fuel price API: {err}") from err

        best: dict = {}

        for station_entry in raw.get("fuelPriceDetails", []):
            station = station_entry.get("fuelStation", {})
            location = station.get("location", {})
            try:
                s_lat = float(location["latitude"])
                s_lon = float(location["longitude"])
            except (KeyError, TypeError, ValueError):
                continue

            dist = _haversine_m(home_lat, home_lon, s_lat, s_lon)
            if dist > radius_m:
                continue

            for price_entry in station_entry.get("fuelPrices", []):
                if not price_entry.get("isAvailable", False):
                    continue
                fuel_type: str = price_entry.get("fuelType", "")
                try:
                    price = float(price_entry["price"])
                except (KeyError, TypeError, ValueError):
                    continue

                if fuel_type not in best or price < best[fuel_type]["price"]:
                    best[fuel_type] = {
                        "price": price,
                        "station_name": station.get("name", ""),
                        "address": station.get("address", ""),
                        "phone": station.get("contactPhone", ""),
                        "distance_m": round(dist),
                        "updated_at": price_entry.get("updatedAt", ""),
                    }

        return best
