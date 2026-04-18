# Fuel Price Watch VIC

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A [Home Assistant](https://www.home-assistant.io/) custom component that tracks the **cheapest fuel prices near you** in Victoria, Australia — powered by the [Service Victoria Fair Fuel Open Data API](https://developer.service.vic.gov.au/apis/fuel-prices).

---

## Features

- 🔍 **Finds the cheapest price** for each fuel type within a configurable radius of your location
- 📍 **Flexible location source** — use `zone.home` (fixed) or any `device_tracker` entity for on-the-go tracking
- ⚡ **Smart refresh** — re-fetches data when your device moves more than 250 m (GPS jitter ignored)
- 🛢️ **Supports all VIC fuel types** — U91, P95, P98, Diesel, Premium Diesel, E10, E85, B20, LPG, LNG, CNG
- 📊 **Rich sensor attributes** — cheapest station name, address, phone number, distance, and last updated time
- 🔄 **HACS compatible** — easy install and update via HACS

---

## Prerequisites

1. **Home Assistant** 2023.x or later
2. A **Service Victoria API Consumer ID** — register for free at [service victoria](https://service.vic.gov.au/find-services/transport-and-driving/servo-saver/help-centre/servo-saver-public-api)

---

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant → **Integrations**
2. Click the three-dot menu (⋮) → **Custom repositories**
3. Add `https://github.com/qunh/fuel-price-watch-vic` with category **Integration**
4. Search for **Fuel Price Watch VIC** and install it
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/fuel_price_watch_vic` folder into your HA `config/custom_components/` directory
2. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Fuel Price Watch VIC**
3. Enter your **Consumer ID** (from Service Victoria developer portal)
4. Set the **search radius** in km (default: 5 km, max: 100 km)
5. Choose your **location source**:
   - `zone.home` *(default)* — uses your home coordinates
   - Any `device_tracker.*` entity — follows a person/device in real time

---

## Sensors

One sensor is created per **fuel type available** within your radius at setup time.

| Entity | Example State | Unit |
|---|---|---|
| `sensor.fuel_price_unleaded_91` | `195.7` | c/L |
| `sensor.fuel_price_premium_unleaded_95` | `205.9` | c/L |
| `sensor.fuel_price_diesel` | `189.5` | c/L |
| *(one per available fuel type)* | | |

### Supported Fuel Types

| Code | Name |
|---|---|
| U91 | Unleaded 91 |
| P95 | Premium Unleaded 95 |
| P98 | Premium Unleaded 98 |
| DSL | Diesel |
| PDSL | Premium Diesel |
| E10 | Ethanol 10 |
| E85 | Ethanol 85 |
| B20 | Biodiesel 20 |
| LPG | LPG |
| LNG | LNG |
| CNG | CNG |

### Sensor Attributes

Each sensor exposes the following extra attributes:

| Attribute | Description |
|---|---|
| `fuel_type` | Fuel type code (e.g. `U91`) |
| `station_name` | Name of the cheapest station |
| `address` | Station address |
| `phone` | Station phone number |
| `distance_m` | Distance to the station in metres |
| `updated_at` | Timestamp of the last price update from the API |

---

## Options

After setup, you can adjust options via **Settings → Devices & Services → Fuel Price Watch VIC → Configure**:

- **Radius (km)** — change the search radius
- **Location source** — switch between `zone.home` and a device tracker

---

## How It Works

1. On a configurable interval (default: **hourly**), the integration fetches all fuel prices across Victoria from the Service Victoria API
2. It calculates the **haversine distance** from your location to each station
3. Stations **outside the configured radius** are filtered out
4. The **lowest price** per fuel type within the radius is exposed as a sensor
5. If using a device tracker, prices are also refreshed whenever you move **more than 250 metres**

> **Note:** The Service Victoria fuel price data is updated approximately every 24 hours, so hourly polling is sufficient and avoids unnecessary API load.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `API authentication failed (401/403)` | Check your Consumer ID in the integration options |
| `Location source not found` | Ensure the device tracker entity exists and is available in HA |
| `No sensors created` | No fuel stations were found within your radius — try increasing it |
| Prices not updating | Check HA logs for errors; confirm the API is reachable from your HA instance |

---

## Contributing

Pull requests and issues are welcome! Please open an [issue](https://github.com/qunh/fuel-price-watch-vic/issues) to report bugs or suggest features.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgements

- [Service Victoria Fair Fuel Open Data](https://developer.service.vic.gov.au/apis/fuel-prices) for providing the public API
- The [Home Assistant](https://www.home-assistant.io/) community for the amazing platform
