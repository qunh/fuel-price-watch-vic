import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fuel Price Watch VIC from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    from .coordinator import FuelPriceCoordinator

    coordinators: dict[str, FuelPriceCoordinator] = {}

    # Auto-discover all person.* entities and create one coordinator per person
    for person_state in hass.states.async_all("person"):
        person_id = person_state.entity_id
        person_name = (
            person_state.attributes.get("friendly_name")
            or person_id.split(".")[-1].replace("_", " ").title()
        )
        coordinator = FuelPriceCoordinator(hass, entry, person_id, person_name)
        try:
            await coordinator.async_config_entry_first_refresh()
        except Exception as err:
            _LOGGER.warning(
                "Initial fetch failed for '%s': %s — will retry on next poll", person_id, err
            )
        coordinator._register_location_listener()
        coordinators[person_id] = coordinator

    # Fall back to zone.home if no person entities exist or all failed
    if not coordinators:
        _LOGGER.debug("No person entities found; using zone.home as location source")
        coordinator = FuelPriceCoordinator(hass, entry, "zone.home", "Home")
        await coordinator.async_config_entry_first_refresh()
        coordinators["zone.home"] = coordinator

    hass.data[DOMAIN][entry.entry_id] = coordinators

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinators: dict = hass.data[DOMAIN].get(entry.entry_id, {})
    for coordinator in coordinators.values():
        coordinator._unregister_location_listener()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
