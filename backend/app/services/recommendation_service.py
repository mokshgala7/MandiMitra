from typing import Dict, Any, Optional
from app.services.mandi_service import MandiService
from app.services.prediction_service import PredictionService
from app.services.weather_service import WeatherService

class RecommendationService:
    def __init__(self, mandi_service: MandiService, prediction_service: PredictionService):
        self.mandi_service = mandi_service
        self.prediction_service = prediction_service

    def generate_recommendation(
        self,
        crop: str,
        quantity_kg: float,
        latitude: float,
        longitude: float,
        has_middleman: bool = False,
        middleman_price: Optional[float] = None,
        middleman_commission: Optional[float] = None,
        middleman_other: Optional[float] = None,
        radius_km: float = 500.0
    ) -> Dict[str, Any]:
        crop_clean = crop.strip().lower()
        quantity_quintals = round(quantity_kg / 100.0, 2)

        # 1. Fetch nearby mandis within 500 km
        nearby_data = self.mandi_service.get_nearby_mandis(
            crop=crop_clean,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km
        )
        mandis_list = nearby_data.get("mandis", [])
        if not mandis_list:
            raise ValueError(f"No mandis found with available prices within {radius_km} km for {crop}.")

        # 2. Evaluate transport and economics for every qualifying mandi
        evaluated_mandis = []
        for m in mandis_list:
            dist = float(m["distance_km"])
            price = float(m["latest_price"])
            # Transportation: ₹10 per KM, ONE-WAY
            transport_cost = round(dist * 10.0, 2)
            gross = round(quantity_quintals * price, 2)
            net = round(gross - transport_cost, 2)

            evaluated_mandis.append({
                "mandi_id": m["mandi_id"],
                "mandi_name": m["mandi_name"],
                "district": m["district"],
                "state": m["state"],
                "distance_km": dist,
                "price_per_quintal": price,
                "transport_cost": transport_cost,
                "gross_value": gross,
                "net_value": net
            })

        # Best mandi is strictly the one with the maximum net value after transport
        best_mandi = max(evaluated_mandis, key=lambda x: x["net_value"])

        # 3. Middleman comparison
        middleman_eco = None
        if has_middleman and middleman_price and middleman_price > 0:
            comm = float(middleman_commission or 0.0)
            other = float(middleman_other or 0.0)
            m_gross = round(quantity_quintals * float(middleman_price), 2)
            m_net = round(m_gross - comm - other, 2)
            middleman_eco = {
                "price_per_quintal": round(float(middleman_price), 2),
                "commission": comm,
                "other_charges": other,
                "gross_value": m_gross,
                "net_value": m_net
            }

        # Current best selling net value today
        current_mandi_net = best_mandi["net_value"]
        current_net = current_mandi_net
        if middleman_eco and middleman_eco["net_value"] > current_mandi_net:
            current_net = middleman_eco["net_value"]

        # 4. ML price prediction for the best mandi
        try:
            pred = self.prediction_service.predict(
                crop=crop_clean,
                market=best_mandi["mandi_name"]
            )
            day_3_price = float(pred["forecast"]["day_3"])
            trend = pred.get("trend", "stable")
        except Exception:
            # Fallback if specific mandi has short history
            day_3_price = best_mandi["price_per_quintal"]
            trend = "stable"

        # Expected future net value at Day 3 (using best mandi)
        expected_future_gross = round(quantity_quintals * day_3_price, 2)
        expected_future_net = round(expected_future_gross - best_mandi["transport_cost"], 2)
        potential_diff = round(expected_future_net - current_net, 2)

        # 5. Weather advisory
        weather = WeatherService.get_weather(latitude, longitude)
        weather_advisory = weather.get("alert")

        # 6. Final Decision Rule
        # HOLD if future net improves by > 2% AND trend is rising
        threshold = current_net * 0.02
        if potential_diff > threshold and trend == "rising":
            recommendation = "HOLD FOR 2–3 DAYS"
            reason = (
                f"ML price models project {crop.capitalize()} prices rising to ₹{day_3_price:.2f}/quintal in 3 days. "
                f"Holding your {quantity_quintals} quintals can increase your net payout by ₹{potential_diff:,.2f} "
                f"at {best_mandi['mandi_name']}."
            )
        else:
            recommendation = "SELL TODAY"
            if middleman_eco and middleman_eco["net_value"] > current_mandi_net:
                reason = (
                    f"Selling to your local buyer yields ₹{middleman_eco['net_value']:,.2f}, which exceeds "
                    f"{best_mandi['mandi_name']}'s net value (₹{current_mandi_net:,.2f}) after transport costs. "
                    f"Future market price upside is limited or negative."
                )
            else:
                reason = (
                    f"Today's net payout of ₹{best_mandi['net_value']:,.2f} at {best_mandi['mandi_name']} "
                    f"(after ₹{best_mandi['transport_cost']:.2f} transport) is optimal. "
                    f"Holding does not offer sufficient economic upside (<2%) to justify storage and spoilage risks."
                )

        return {
            "recommendation": recommendation,
            "reason": reason,
            "crop": crop_clean,
            "quantity_kg": quantity_kg,
            "quantity_quintals": quantity_quintals,
            "best_mandi": best_mandi,
            "middleman": middleman_eco,
            "current_net_value": round(current_net, 2),
            "expected_future_price": round(day_3_price, 2),
            "expected_future_net_value": round(expected_future_net, 2),
            "potential_difference": round(potential_diff, 2),
            "trend": trend,
            "weather_advisory": weather_advisory
        }
