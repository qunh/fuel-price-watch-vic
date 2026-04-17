import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_FUEL_TYPE, CONF_SUBURB, CONF_POSTCODE, FUEL_TYPES


class FuelPriceWatchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Fuel Price Watch VIC."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_POSTCODE]}_{user_input[CONF_FUEL_TYPE]}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"{user_input[CONF_SUBURB]} - {user_input[CONF_FUEL_TYPE]}",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_SUBURB): str,
                vol.Required(CONF_POSTCODE): str,
                vol.Required(CONF_FUEL_TYPE): vol.In(FUEL_TYPES),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        return FuelPriceWatchOptionsFlow(entry)


class FuelPriceWatchOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, entry: config_entries.ConfigEntry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "scan_interval",
                        default=self.entry.options.get("scan_interval", 3600),
                    ): int,
                }
            ),
        )
