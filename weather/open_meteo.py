"""
Weather Lookup — Open-Meteo
--------------------------------
Turns a plain location name (e.g. "Rongai") into current weather
conditions, using Open-Meteo's free geocoding + forecast APIs.
No API key required for either endpoint.

This only runs when Call 1 sets weather_required-style context
(e.g. intent is irrigation_weather, or crop planning mentions rain).
"""

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(location: str) -> dict:
    """
    Takes a place name and returns a small, predictable weather dict.
    Always returns a usable dict — never raises — so a weather
    failure never crashes the whole app; it just means Call 2
    proceeds without weather context.
    """

    # --- Step 1: turn the location name into coordinates ---
    try:
        geo_response = requests.get(
            GEOCODING_URL,
            params={"name": location, "count": 1, "language": "en"},
            timeout=8,
        )
        geo_response.raise_for_status()
        geo_data = geo_response.json()
    except (requests.RequestException, ValueError) as e:
        return _fallback(location, error=f"geocoding_failed: {e}")

    results = geo_data.get("results")
    if not results:
        return _fallback(location, error="location_not_found")

    place = results[0]
    latitude = place["latitude"]
    longitude = place["longitude"]
    matched_name = place.get("name", location)

    # --- Step 2: fetch the current weather for those coordinates ---
    try:
        forecast_response = requests.get(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                "timezone": "auto",
            },
            timeout=8,
        )
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
    except (requests.RequestException, ValueError) as e:
        return _fallback(location, error=f"forecast_failed: {e}")

    current = forecast_data.get("current", {})

    # --- This is the exact shape Call 2 will receive ---
    return {
        "location": matched_name,
        "latitude": latitude,
        "longitude": longitude,
        "temperature_c": current.get("temperature_2m"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "precipitation_mm": current.get("precipitation"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "available": True,
        "error": None,
    }


def _fallback(location: str, error: str) -> dict:
    """Consistent shape returned when weather can't be fetched."""
    return {
        "location": location,
        "latitude": None,
        "longitude": None,
        "temperature_c": None,
        "humidity_percent": None,
        "precipitation_mm": None,
        "wind_speed_kmh": None,
        "available": False,
        "error": error,
    }


# --- Quick manual test from the command line ---
if __name__ == "__main__":
    place = input("Enter a location to test (e.g. Rongai): ")
    result = get_weather(place)
    import json
    print(json.dumps(result, indent=2))