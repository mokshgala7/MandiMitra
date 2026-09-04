"""
weather_features.py — MandiMitra Weather Interface

Accepts external weather information and validates it.
Does NOT fetch or fabricate weather data.
The recommendation system works fully without weather.
"""

from typing import Any, Dict, Optional

NOT_AVAILABLE = "NOT_AVAILABLE"

VALID_FIELDS = {
    "temperature": (float, int),
    "rainfall_mm": (float, int),
    "rain_probability": (float, int),
    "weather_alert": bool,
    "humidity_pct": (float, int),
    "wind_speed_kmh": (float, int),
}


def validate_weather(weather_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate and normalize external weather data.
    Returns weather dict with status flag.

    Parameters
    ----------
    weather_data : dict or None — externally provided weather fields

    Returns
    -------
    dict with status and validated fields
    """
    if not weather_data:
        return {"weather_status": NOT_AVAILABLE, "note": "No weather data provided."}

    validated = {"weather_status": "AVAILABLE"}
    warnings = []

    for field, expected_types in VALID_FIELDS.items():
        if field in weather_data:
            val = weather_data[field]
            if not isinstance(val, expected_types):
                warnings.append(f"Field '{field}' expected {expected_types}, got {type(val).__name__}; skipped.")
            else:
                validated[field] = val

    # Range checks
    if "rain_probability" in validated:
        rp = validated["rain_probability"]
        if not (0 <= rp <= 1):
            if 0 <= rp <= 100:
                validated["rain_probability"] = rp / 100  # normalize 0-100 → 0-1
            else:
                warnings.append("rain_probability out of range [0,1]; ignored.")
                del validated["rain_probability"]

    if "humidity_pct" in validated:
        hp = validated["humidity_pct"]
        if not (0 <= hp <= 100):
            warnings.append(f"humidity_pct={hp} out of [0,100]; ignored.")
            del validated["humidity_pct"]

    if warnings:
        validated["warnings"] = warnings

    return validated


def weather_summary(validated_weather: Dict[str, Any]) -> str:
    """Produce a human-readable one-line weather summary for explanations."""
    if validated_weather.get("weather_status") == NOT_AVAILABLE:
        return "No weather data available."
    parts = []
    if "temperature" in validated_weather:
        parts.append(f"Temp: {validated_weather['temperature']}°C")
    if "rainfall_mm" in validated_weather:
        parts.append(f"Rainfall: {validated_weather['rainfall_mm']}mm")
    if validated_weather.get("weather_alert"):
        parts.append("⚠ WEATHER ALERT active")
    if "rain_probability" in validated_weather:
        rp = validated_weather["rain_probability"]
        parts.append(f"Rain prob: {rp*100:.0f}%")
    return " | ".join(parts) if parts else "Weather data available but no notable conditions."


if __name__ == "__main__":
    tests = [
        None,
        {"temperature": 32, "rainfall_mm": 0, "rain_probability": 0.15, "weather_alert": False},
        {"temperature": 28, "rainfall_mm": 50, "rain_probability": 85, "weather_alert": True},
    ]
    for t in tests:
        r = validate_weather(t)
        print(f"  Status: {r.get('weather_status')} | Summary: {weather_summary(r)}")
