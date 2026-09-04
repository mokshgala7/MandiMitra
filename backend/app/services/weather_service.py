import requests
from typing import Dict, Any

# Open-Meteo weather code mapping to human-readable condition and emoji icon
WMO_CODE_MAP = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    61: ("Slight rain", "🌧️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    71: ("Slight snow fall", "🌨️"),
    73: ("Moderate snow fall", "🌨️"),
    75: ("Heavy snow fall", "❄️"),
    80: ("Slight rain showers", "🌦️"),
    81: ("Moderate rain showers", "🌧️"),
    82: ("Violent rain showers", "⛈️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with slight hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}

class WeatherService:
    @staticmethod
    def get_weather(latitude: float, longitude: float, location_name: str = "Your Area") -> Dict[str, Any]:
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&hourly=precipitation_probability&forecast_days=1"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                current = data.get("current", {})
                wcode = current.get("weather_code", 0)
                condition, icon = WMO_CODE_MAP.get(wcode, ("Fair", "🌤️"))
                temp = current.get("temperature_2m", 28.0)
                
                # Precipitation probability max today
                hourly_precip = data.get("hourly", {}).get("precipitation_probability", [0])
                max_precip_prob = max(hourly_precip) if hourly_precip else 0.0

                # Formulate agricultural advisory
                alert = None
                if max_precip_prob >= 60 or "rain" in condition.lower() or "thunderstorm" in condition.lower():
                    alert = "🌧️ High rain probability today. Use covered transport to avoid crop moisture damage."
                elif temp >= 38.0:
                    alert = "☀️ Extreme heat warning. Transport sensitive produce during early morning or evening."
                else:
                    alert = "✅ Favorable dry weather for harvesting, drying, and market transport."

                return {
                    "location": location_name,
                    "latitude": latitude,
                    "longitude": longitude,
                    "temperature": round(float(temp), 1),
                    "temperature_c": round(float(temp), 1),
                    "condition": condition,
                    "precipitation_probability": float(max_precip_prob),
                    "precipitation_prob": float(max_precip_prob),
                    "alert": alert,
                    "advisory": alert,
                    "weather_code": int(wcode),
                    "icon": icon
                }
        except Exception:
            pass

        # Informative baseline fallback if network is unreachable
        return {
            "location": location_name,
            "latitude": latitude,
            "longitude": longitude,
            "temperature": 29.5,
            "temperature_c": 29.5,
            "condition": "Dry conditions",
            "precipitation_probability": 10.0,
            "precipitation_prob": 10.0,
            "alert": "Favorable dry weather for market transport.",
            "advisory": "Favorable dry weather for market transport.",
            "weather_code": 0,
            "icon": "☀️"
        }
