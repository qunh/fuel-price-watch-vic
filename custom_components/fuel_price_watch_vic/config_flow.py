import uuid

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    API_PRICES_ENDPOINT,
    CONF_CONSUMER_ID,
    CONF_LOCATION_SOURCE,
    CONF_RADIUS_KM,
    DEFAULT_LOCATION_SOURCE,
    DEFAULT_RADIUS_KM,
    DOMAIN,
    USER_AGENT,
)


class FuelPriceWatchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Fuel Price Watch VIC."""

    VERSION = 1

    def __init__(self):
        self._data: dict = {}

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            consumer_id = user_input[CONF_CONSUMER_ID].strip()
            try:
                await _validate_consumer_id(consumer_id)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(consumer_id)
                self._abort_if_unique_id_configured()
                self._data = {
                    CONF_CONSUMER_ID: consumer_id,
                    CONF_RADIUS_KM: user_input[CONF_RADIUS_KM],
                }
                return await self.async_step_location()

        schema = vol.Schema(
            {
                vol.Required(CONF_CONSUMER_ID): str,
                vol.Required(CONF_RADIUS_KM, default=DEFAULT_RADIUS_KM): vol.All(
                    int, vol.Range(min=1, max=100)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_location(self, user_input=None):
        """Step 2 – pick the location source (zone.home or a device tracker)."""
        if user_input is not None:
            self._data[CONF_LOCATION_SOURCE] = user_input[CONF_LOCATION_SOURCE]
            return self.async_create_entry(title="Fuel Price Watch VIC", data=self._data)

        # Build list of options: zone.home first, then all device_tracker.* entities
        options = [DEFAULT_LOCATION_SOURCE] + sorted(
            state.entity_id
            for state in self.hass.states.async_all("device_tracker")
        )

        return self.async_show_form(
            step_id="location",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_LOCATION_SOURCE, default=DEFAULT_LOCATION_SOURCE
                    ): vol.In(options),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        return FuelPriceWatchOptionsFlow(entry)


class FuelPriceWatchOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Build device tracker list the same way as the config flow
        options = [DEFAULT_LOCATION_SOURCE] + sorted(
            state.entity_id
            for state in self.hass.states.async_all("device_tracker")
        )

        current_location = self.config_entry.options.get(
            CONF_LOCATION_SOURCE,
            self.config_entry.data.get(CONF_LOCATION_SOURCE, DEFAULT_LOCATION_SOURCE),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_RADIUS_KM,
                        default=self.config_entry.options.get(
                            CONF_RADIUS_KM,
                            self.config_entry.data.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM),
                        ),
                    ): vol.All(int, vol.Range(min=1, max=100)),
                    vol.Required(
                        CONF_LOCATION_SOURCE, default=current_location
                    ): vol.In(options),
                }
            ),
        )


async def _validate_consumer_id(consumer_id: str) -> None:
    """Raise InvalidAuth or CannotConnect if the consumer ID does not work."""
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
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status in (401, 403):
                    raise InvalidAuth
                resp.raise_for_status()
    except InvalidAuth:
        raise
    except aiohttp.ClientError as err:
        raise CannotConnect from err


class CannotConnect(Exception):
    pass


class InvalidAuth(Exception):
    pass
