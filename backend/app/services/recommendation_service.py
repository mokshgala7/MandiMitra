from typing import Dict, Any, Optional, List
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
        crop_title = crop.strip().capitalize()
        quantity_quintals = round(quantity_kg / 100.0, 2)

        # 1. Fetch nearby mandis within radius
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
            # Transportation: ₹10 per KM, ONE-WAY (using rounded km for consistent display)
            transport_cost = round(round(dist) * 10.0, 2)
            gross = round(quantity_quintals * price, 2)
            net = round(gross - transport_cost, 2)

            evaluated_mandis.append({
                "mandi_id": m["mandi_id"],
                "mandi_name": m["mandi_name"],
                "district": m.get("district", ""),
                "state": m.get("state", ""),
                "distance_km": dist,
                "price_per_quintal": price,
                "transport_cost": transport_cost,
                "gross_value": gross,
                "net_value": net
            })

        # Best mandi is strictly the one with the maximum net value today after transport
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

        current_mandi_net = best_mandi["net_value"]
        current_net = current_mandi_net
        is_middleman_best = False
        if middleman_eco and middleman_eco["net_value"] > current_mandi_net:
            current_net = middleman_eco["net_value"]
            is_middleman_best = True

        # 4. Compute ML 2-3 day forecast & recommendation for EACH AND EVERY MANDI
        mandi_recommendations: List[Dict[str, Any]] = []
        for m in evaluated_mandis:
            m_name = m["mandi_name"]
            c_price = m["price_per_quintal"]
            c_net = m["net_value"]
            tc = m["transport_cost"]
            dist = m["distance_km"]

            # ML prediction for this specific market
            try:
                pred = self.prediction_service.predict(crop=crop_clean, market=m_name)
                fut_price = float(pred["forecast"]["day_3"])
                m_trend = pred.get("trend", "stable")
            except Exception:
                fut_price = c_price
                m_trend = "stable"

            fut_gross = round(quantity_quintals * fut_price, 2)
            fut_net = round(fut_gross - tc, 2)
            diff = round(fut_net - c_net, 2)

            # Decision logic for this individual mandi
            if diff > (c_net * 0.02) and m_trend == "rising":
                m_decision = "HOLD FOR 2–3 DAYS"
                m_pct = round(((fut_net - c_net) / c_net) * 100, 1) if c_net > 0 else 0.0
                m_adv = diff
                m_reason = (
                    f"It is better to HOLD and sell after 2 to 3 days by {m_pct}% (+₹{m_adv:,.2f})! "
                    f"Based on ML price forecasts for {m_name}, {crop_title} prices are projected to rise from "
                    f"₹{c_price:,.2f} to ₹{fut_price:,.2f}/quintal in 2–3 days. "
                    f"Waiting 2–3 days earns you ₹{m_adv:,.2f} MORE net payout "
                    f"(predicted future net: ₹{fut_net:,.2f} vs ₹{c_net:,.2f} today)."
                )
            else:
                m_decision = "SELL TODAY"
                if fut_net < c_net:
                    drop_amt = round(c_net - fut_net, 2)
                    m_adv = drop_amt
                    # Percentage advantage of selling today vs future
                    m_pct = round(((c_net - fut_net) / fut_net) * 100, 1) if fut_net > 0 else round(((c_net - fut_net) / c_net) * 100, 1)
                    m_reason = (
                        f"It is better to SELL TODAY by {m_pct}% (+₹{drop_amt:,.2f}) compared to waiting 2 to 3 days! "
                        f"Based on ML price forecasts for {m_name}, {crop_title} prices are forecasted to fall from "
                        f"₹{c_price:,.2f} to ₹{fut_price:,.2f}/quintal in 2–3 days. "
                        f"Selling today at {m_name} earns you ₹{drop_amt:,.2f} MORE net payout "
                        f"(today's net: ₹{c_net:,.2f} vs predicted future net: ₹{fut_net:,.2f})."
                    )
                else:
                    m_adv = 0.0
                    m_pct = round(abs(((fut_net - c_net) / c_net) * 100), 1) if c_net > 0 else 0.0
                    m_reason = (
                        f"It is better to SELL TODAY! Based on ML price forecasts for {m_name}, {crop_title} prices will remain "
                        f"approximately stable (~₹{fut_price:,.2f}/quintal) with negligible upside (+{m_pct}%). "
                        f"Selling today at {m_name} locks in ₹{c_net:,.2f} net immediately without crop storage or weather risks."
                    )

            mandi_recommendations.append({
                "mandi_id": m["mandi_id"],
                "mandi_name": m_name,
                "district": m["district"],
                "state": m["state"],
                "distance_km": dist,
                "current_price": c_price,
                "transport_cost": tc,
                "current_gross": m["gross_value"],
                "current_net": c_net,
                "future_price": round(fut_price, 2),
                "future_gross": fut_gross,
                "future_net": fut_net,
                "potential_diff": diff,
                "better_decision": m_decision,
                "better_percentage": m_pct,
                "advantage_amount": m_adv,
                "trend": m_trend,
                "reason": m_reason,
                "is_best": (m["mandi_id"] == best_mandi["mandi_id"])
            })

        # 5. Extract Best Mandi's future projection for the overall recommendation
        best_rec = next((item for item in mandi_recommendations if item["mandi_id"] == best_mandi["mandi_id"]), mandi_recommendations[0] if mandi_recommendations else None)
        if best_rec:
            day_3_price = best_rec["future_price"]
            expected_future_net = best_rec["future_net"]
            trend = best_rec["trend"]
        else:
            day_3_price = curr_mandi_price
            expected_future_net = current_mandi_net
            trend = "stable"
        potential_diff = round(expected_future_net - current_net, 2)

        # 6. Weather advisory
        weather = WeatherService.get_weather(latitude, longitude)
        weather_advisory = weather.get("alert")

        # 7. Final Overall Recommendation & Clear Statements
        threshold = current_net * 0.02
        best_mandi_name = best_mandi["mandi_name"]
        curr_mandi_price = best_mandi["price_per_quintal"]

        if potential_diff > threshold and trend == "rising":
            recommendation = "HOLD FOR 2–3 DAYS"
            better_decision = "HOLD FOR 2–3 DAYS"
            better_percentage = round(((expected_future_net - current_net) / current_net) * 100, 1)
            more_amount = round(potential_diff, 2)
            reason = (
                f"It is better to HOLD and sell after 2 to 3 days by {better_percentage}% (+₹{more_amount:,.2f})! "
                f"Based on ML price forecasts for {best_mandi_name}, {crop_title} prices are projected to rise from "
                f"₹{curr_mandi_price:,.2f} to ₹{day_3_price:,.2f}/quintal in 2–3 days. "
                f"Waiting 2–3 days earns you ₹{more_amount:,.2f} MORE net payout "
                f"(predicted future net: ₹{expected_future_net:,.2f} vs ₹{current_net:,.2f} today)."
            )
        else:
            recommendation = "SELL TODAY"
            better_decision = "SELL TODAY"
            if potential_diff < 0:
                more_amount = round(abs(potential_diff), 2)
                better_percentage = round(((current_net - expected_future_net) / expected_future_net) * 100, 1) if expected_future_net > 0 else round(((current_net - expected_future_net) / current_net) * 100, 1)
                if is_middleman_best:
                    reason = (
                        f"It is better to SELL TODAY by {better_percentage}% (+₹{more_amount:,.2f}) compared to waiting 2 to 3 days! "
                        f"Selling to your local buyer today yields ₹{current_net:,.2f} net (₹{current_net - current_mandi_net:,.2f} more than "
                        f"{best_mandi_name}'s net today of ₹{current_mandi_net:,.2f}). "
                        f"Waiting 2–3 days is projected to net only ₹{expected_future_net:,.2f} at {best_mandi_name} as prices drop from "
                        f"₹{curr_mandi_price:,.2f} to ₹{day_3_price:,.2f}/quintal. Selling today protects you against a ₹{more_amount:,.2f} drop."
                    )
                else:
                    reason = (
                        f"It is better to SELL TODAY by {better_percentage}% (+₹{more_amount:,.2f}) compared to waiting 2 to 3 days! "
                        f"Based on ML price forecasts for {best_mandi_name}, {crop_title} prices are forecasted to fall from "
                        f"₹{curr_mandi_price:,.2f} to ₹{day_3_price:,.2f}/quintal in 2–3 days. "
                        f"Selling today at {best_mandi_name} earns you ₹{more_amount:,.2f} MORE net payout "
                        f"(today's net: ₹{current_net:,.2f} vs predicted future net: ₹{expected_future_net:,.2f})."
                    )
            else:
                more_amount = 0.0
                better_percentage = round(abs(((expected_future_net - current_net) / current_net) * 100), 1) if current_net > 0 else 0.0
                if is_middleman_best:
                    reason = (
                        f"It is better to SELL TODAY! Selling to your local buyer today yields ₹{current_net:,.2f} net "
                        f"(₹{current_net - current_mandi_net:,.2f} more than {best_mandi_name}'s net today). "
                        f"Future market prices at {best_mandi_name} will remain flat (~₹{day_3_price:,.2f}/quintal) with negligible upside (<2%). "
                        f"Selling today locks in maximum profit immediately without crop storage or weather risks."
                    )
                else:
                    reason = (
                        f"It is better to SELL TODAY! Based on ML price forecasts for {best_mandi_name}, prices will remain approximately stable "
                        f"(~₹{day_3_price:,.2f}/quintal) with negligible upside (<2%). "
                        f"Today's net payout of ₹{current_net:,.2f} at {best_mandi_name} is optimal; waiting offers insufficient upside to justify storage costs and weather risks."
                    )

        return {
            "recommendation": recommendation,
            "better_decision": better_decision,
            "better_percentage": better_percentage,
            "statement": reason,
            "potentially_more_amount": more_amount,
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
            "weather_advisory": weather_advisory,
            "mandi_recommendations": mandi_recommendations
        }
