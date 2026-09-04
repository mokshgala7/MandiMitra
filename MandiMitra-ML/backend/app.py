from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
from dotenv import load_dotenv
import os


# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()


# ==========================================
# SUPABASE CONNECTION
# ==========================================

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


# ==========================================
# FLASK APP
# ==========================================

app = Flask(__name__)
CORS(app)


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return jsonify({
        "message": "MandiMitra Backend is Running!"
    })


# ==========================================
# USERS - GET AND POST
# ==========================================

@app.route("/api/users", methods=["GET", "POST"])
def users():

    # GET ALL USERS
    if request.method == "GET":

        response = supabase.table("users").select("*").execute()

        return jsonify({
            "users": response.data
        }), 200


    # POST NEW USER

    data = request.json

    response = supabase.table("users").insert({

        "name": data.get("name"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "location": data.get("location")

    }).execute()

    return jsonify({
        "message": "User created successfully",
        "data": response.data
    }), 201


# ==========================================
# SAVED CROPS - GET AND POST
# ==========================================

@app.route("/api/saved-crops", methods=["GET", "POST"])
def saved_crops():

    # GET SAVED CROPS

    if request.method == "GET":

        user_id = request.args.get("user_id")

        query = supabase.table("saved_crops").select("*")

        # Filter by user_id if provided
        if user_id:
            query = query.eq("user_id", user_id)

        response = query.execute()

        return jsonify({
            "saved_crops": response.data
        }), 200


    # POST NEW SAVED CROP

    data = request.json

    response = supabase.table("saved_crops").insert({

        "user_id": data.get("user_id"),
        "crop_name": data.get("crop_name")

    }).execute()

    return jsonify({
        "message": "Crop saved successfully",
        "data": response.data
    }), 201


# ==========================================
# MARKET PRICES - GET AND POST
# ==========================================

@app.route("/api/market-prices", methods=["GET", "POST"])
def market_prices():

    # GET MARKET PRICES

    if request.method == "GET":

        crop = request.args.get("crop")
        city = request.args.get("city")

        query = supabase.table("market_prices").select("*")

        # Filter by crop
        if crop:
            query = query.eq("crop_name", crop)

        # Filter by city
        if city:
            query = query.eq("city", city)

        response = query.execute()

        return jsonify({
            "market_prices": response.data
        }), 200


    # POST MARKET PRICE

    data = request.json

    response = supabase.table("market_prices").insert({

        "crop_name": data.get("crop_name"),
        "mandi_name": data.get("mandi_name"),
        "city": data.get("city"),
        "price": data.get("price"),
        "price_date": data.get("price_date")

    }).execute()

    return jsonify({
        "message": "Market price added successfully",
        "data": response.data
    }), 201


# ==========================================
# GET PRICE HISTORY
# ==========================================

@app.route("/api/price-history/<crop_name>", methods=["GET"])
def get_price_history(crop_name):

    response = (
        supabase
        .table("market_prices")
        .select("*")
        .eq("crop_name", crop_name)
        .order("price_date")
        .execute()
    )

    return jsonify(response.data), 200


# ==========================================
# MANDI ANALYSIS
# ==========================================

@app.route("/api/mandi-analysis", methods=["POST"])
def mandi_analysis():

    data = request.json

    crop = data.get("crop")
    location = data.get("location")


    # GET REAL MARKET PRICE DATA FROM SUPABASE

    response = (
        supabase
        .table("market_prices")
        .select("*")
        .eq("crop_name", crop)
        .execute()
    )

    mandis = response.data


    # CHECK IF DATA EXISTS

    if not mandis:

        return jsonify({
            "message": f"No market price data found for {crop}"
        }), 404


    # FIND MANDI WITH HIGHEST PRICE

    best_mandi = max(
        mandis,
        key=lambda x: float(x["price"])
    )


    # RETURN ANALYSIS

    return jsonify({

        "crop": crop,

        "farmer_location": location,

        "mandis": mandis,

        "recommendation": {

            "best_mandi": best_mandi["mandi_name"],

            "city": best_mandi["city"],

            "best_price": best_mandi["price"],

            "message": (
                f"Best available price for {crop} "
                f"is currently in {best_mandi['city']}"
            )

        }

    }), 200


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)