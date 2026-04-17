DOMAIN = "fuel_price_watch_vic"

CONF_CONSUMER_ID = "consumer_id"
CONF_RADIUS_KM = "radius_km"
CONF_LOCATION_SOURCE = "location_source"

DEFAULT_RADIUS_KM = 5
DEFAULT_LOCATION_SOURCE = "zone.home"
DEFAULT_SCAN_INTERVAL = 3600  # API data is ~24h delayed; hourly refresh is sufficient

API_BASE_URL = "https://api.fuel.service.vic.gov.au/open-data/v1"
API_PRICES_ENDPOINT = f"{API_BASE_URL}/fuel/prices"
USER_AGENT = "FuelPriceWatchVIC/2.0"

# All fuel type codes supported by the Service Victoria Fair Fuel Open Data API
FUEL_TYPES: dict[str, str] = {
    "U91": "Unleaded 91",
    "P95": "Premium Unleaded 95",
    "P98": "Premium Unleaded 98",
    "DSL": "Diesel",
    "PDSL": "Premium Diesel",
    "E10": "Ethanol 10",
    "E85": "Ethanol 85",
    "B20": "Biodiesel 20",
    "LPG": "LPG",
    "LNG": "LNG",
    "CNG": "CNG",
}
