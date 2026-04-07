from flask import Flask, request, jsonify
import requests
from collections import OrderedDict
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.json.sort_keys = False

# ---------------- DATABASE ---------------- #

DB_NAME = "history.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        food_name TEXT,
        sugar REAL,
        sodium REAL,
        fat REAL,
        protein REAL,
        calories REAL,
        health_score INTEGER,
        category TEXT,
        verdict TEXT,
        image TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


def save_to_history(data, score, category, verdict):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO history (
        food_name, sugar, sodium, fat, protein, calories,
        health_score, category, verdict, image, timestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["sugar"],
        data["sodium"],
        data["fat"],
        data["protein"],
        data["calories"],
        score,
        category,
        verdict,
        data.get("image", ""),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

# ---------------- HEALTH LOGIC ---------------- #

def calculate_score(sugar, sodium, fat):
    score = 10

    if sugar > 10:
        score -= 2
    if sugar > 20:
        score -= 3
    if sugar > 40:
        score -= 2

    if sodium > 300:
        score -= 2
    if sodium > 600:
        score -= 3

    if fat > 20:
        score -= 2

    return max(score, 0)


def get_category(score):
    return "Safe" if score >= 7 else "Moderate" if score >= 4 else "Avoid"


def get_verdict(score):
    return (
        "✅ Safe to consume"
        if score >= 7 else
        "⚠️ Consume in moderation"
        if score >= 4 else
        "🚫 Avoid this product"
    )


def get_color(score):
    return "green" if score >= 7 else "orange" if score >= 4 else "red"

# ---------------- ALERTS ---------------- #

def get_alerts(sugar, sodium):
    alerts = []

    if sugar > 40:
        alerts.append("⚠️ Extremely high sugar – Avoid completely")
    elif sugar > 15:
        alerts.append("⚠️ High sugar – Limit intake")

    if sodium > 600:
        alerts.append("⚠️ Very high sodium – Risk for BP")
    elif sodium > 300:
        alerts.append("⚠️ Moderate sodium – Be careful")

    return alerts

# ---------------- DAILY LIMIT ---------------- #

def get_daily_limits(sugar, sodium):
    return {
        "sugar_%": min(round((sugar / 25) * 100, 2), 100),
        "sodium_%": min(round((sodium / 2000) * 100, 2), 100)
    }

# ---------------- ALTERNATIVES ---------------- #

PRODUCT_ALTERNATIVES = {
    "maggi": ["Oats", "Vegetable Upma"],
    "lays": ["Roasted Makhana", "Baked Chips"],
    "kurkure": ["Roasted Snacks"],
    "oreo": ["Dark Chocolate"],
    "dairy milk": ["Dark Chocolate (70%)"]
}

HEALTHY_ALTERNATIVES = {
    "high_sugar": ["Fruits", "Oats"],
    "drinks": [
        "Coconut Water",
        "Lemon Water",
        "Fresh Juice (No Sugar)"
    ],
    "high_sodium": ["Roasted Chana"],
    "high_fat": ["Popcorn"]
}

def suggest_alternatives(name, sugar, sodium, fat, category=""):
    name = name.lower()

    for key in PRODUCT_ALTERNATIVES:
        if key in name:
            return PRODUCT_ALTERNATIVES[key]

    suggestions = []

    if "drink" in name or "drink" in category:
        suggestions.extend(HEALTHY_ALTERNATIVES["drinks"])

    if sugar > 15:
        suggestions.extend(HEALTHY_ALTERNATIVES["high_sugar"])
    if sodium > 500:
        suggestions.extend(HEALTHY_ALTERNATIVES["high_sodium"])
    if fat > 20:
        suggestions.extend(HEALTHY_ALTERNATIVES["high_fat"])

    return list(set(suggestions))

# ---------------- LOCAL DATA ---------------- #
INDIAN_PRODUCTS = {

   #----------snacks---------#

     "kurkure": {
        "name": "Kurkure",
        "category": "Snack", 
        "sugar": 1.0,
        "sodium": 892,
        "fat": 34.6,
        "protein": 6.4,
        "calories": 558,
        "image": "https://m.media-amazon.com/images/I/81z5Z6n6VxL.jpg",
        "barcode": "8901491435109"
    },

    "lays": {
        "name": "Lays Chips",
        "category": "Snack", 
        "sugar": 1.2,
        "sodium": 650,
        "fat": 34.0,
        "protein": 6.0,
        "calories": 536,
        "image": "https://m.media-amazon.com/images/I/61XzLZ5wFLL.jpg",
        "barcode": "8901491101103"
    },

    "aloo_bhujia": {
        "name": "Aloo Bhujia",
        "category": "Snack",
        "sugar": 0.25,
        "sodium": 615,
        "fat": 38.12,
        "protein": 8.68,
        "calories": 562,
        "image": "",
        "barcode": "8904004400687"
    },

    "bingo": {
        "name": "Bingo Chips",
        "category": "Snack",
        "sugar": 6,
        "sodium": 758,
        "fat": 29.5,
        "protein": 5.6,
        "calories": 526,
        "image": "",
        "barcode": "8901725181220"
    },

    "uncle_chips": {
        "name": "Uncle Chips",
        "category": "Snack",
        "sugar": 0.6,
        "sodium": 591,
        "fat": 35,
        "protein": 6.7,
        "calories": 550,
        "image": "",
        "barcode": "8901491435109"
    },

    "doritos": {
        "name": "Doritos",
        "category": "Snack",
        "sugar": 4.5,
        "sodium": 605,
        "fat": 23.4,
        "protein": 7.1,
        "calories": 499,
        "image": "",
        "barcode": "8901491102100"
    },

    "too_yumm": {
        "name": "Too Yumm Chips",
        "category": "Snack",
        "sugar": 8.5,
        "sodium": 880,
        "fat": 18.3,
        "protein": 7.9,
        "calories": 464,
        "image": "",
        "barcode": "8906090572064"
    },

    "britannia_cake": {
        "name": "Britannia Little Roll Cake",
        "category": "Cake",
        "sugar": 30.2,
        "sodium": 252.6,
        "fat": 17.3,
        "protein": 5.7,
        "calories": 415,
        "image": "",
        "barcode": "8901063363779"
    },

    "paper_boat": {
        "name": "Paper Boat Drink",
        "category": "Drink",
        "sugar": 13.0,
        "sodium": 40,
        "fat": 0,
        "protein": 0,
        "calories": 52.8,
        "image": "",
        "barcode": "8906080600647"
    },

    "coca_cola": {
        "name": "Coca Cola",
        "category": "Soft Drink",
        "sugar": 10.6,
        "sodium": 8.5,
        "fat": 0,
        "protein": 0,
        "calories": 44,
        "image": "",
        "barcode": "8901764031016"
    },

    "pepsi": {
        "name": "Pepsi",
        "category": "Soft Drink",
        "sugar": 10.9,
        "sodium": 3,
        "fat": 0,
        "protein": 0,
        "calories": 43,
        "image": "",
        "barcode": "8902080015000"
    },

    "maaza": {
        "name": "Maaza Mango Drink",
        "category": "Fruit Drink",
        "sugar": 14.9,
        "sodium": 21.9,
        "fat": 0,
        "protein": 0,
        "calories": 63,
        "image": "",
        "barcode": "8901764092305"
    },

    "frooti": {
        "name": "Frooti",
        "category": "Fruit Drink",
        "sugar": 15.6,
        "sodium": 24.2,
        "fat": 0,
        "protein": 0,
        "calories": 63.2,
        "image": "",
        "barcode": "8902579103057"
    },

    "slice": {
        "name": "Slice Mango Drink",
        "category": "Fruit Drink",
        "sugar": 10.8,
        "sodium": 73,
        "fat": 0,
        "protein": 0,
        "calories": 50,
        "image": "",
        "barcode": "8902080404575"
    },

    "redbull": {
        "name": "Red Bull",
        "category": "Energy Drink",
        "sugar": 39,
        "sodium": 150,
        "fat": 0,
        "protein": 0,
        "calories": 160,
        "image": "",
        "barcode": "9002490100070"
    },

    "monster": {
        "name": "Monster Energy",
        "category": "Energy Drink",
        "sugar": 0,
        "sodium": 370,
        "fat": 0,
        "protein": 0,
        "calories": 10,
        "image": "",
        "barcode": "5060337502719"
    },

    "tiger_biscuit": {
        "name": "Britannia Tiger Biscuit",
        "category": "Biscuit",
        "sugar": 38.3,
        "sodium": 119,
        "fat": 20.3,
        "protein": 5,
        "calories": 493.5,
        "image": "",
        "barcode": "8901063155411"
    },

    "good_day": {
        "name": "Good Day Biscuit",
        "category": "Biscuit",
        "sugar": 35.1,
        "sodium": 97.4,
        "fat": 24.8,
        "protein": 6.4,
        "calories": 438,
        "image": "",
        "barcode": "8901063093287"
    },

    "bourbon": {
        "name": "Bourbon Biscuit",
        "category": "Biscuit",
        "sugar": 60.5,
        "sodium": 151,
        "fat": 15.9,
        "protein": 3.3,
        "calories": 447,
        "image": "",
        "barcode": "6161101251884"
    },

    "chocobakes": {
        "name": "Chocobakes",
        "category": "Biscuit",
        "sugar": 40.3,
        "sodium": 203,
        "fat": 21.9,
        "protein": 3.8,
        "calories": 466,
        "image": "",
        "barcode": "7622201098971"
    },

    "hide_and_seek": {
        "name": "Hide & Seek",
        "category": "Biscuit",
        "sugar": 32.2,
        "sodium": 50,
        "fat": 18,
        "protein": 5.9,
        "calories": 479,
        "image": "",
        "barcode": "8901719104046"
    },

    "marie_gold": {
        "name": "Marie Gold",
        "category": "Biscuit",
        "sugar": 21.2,
        "sodium": 316,
        "fat": 10.6,
        "protein": 7.9,
        "calories": 445,
        "image": "",
        "barcode": "8901063162211"
    },

    "little_hearts": {
        "name": "Little Hearts",
        "category": "Biscuit",
        "sugar": 24,
        "sodium": 309,
        "fat": 19.5,
        "protein": 7.4,
        "calories": 486,
        "image": "",
        "barcode": "8901063203198"
    },

    "dark_fantasy": {
        "name": "Dark Fantasy",
        "category": "Biscuit",
        "sugar": 37.6,
        "sodium": 150,
        "fat": 25,
        "protein": 5.7,
        "calories": 504,
        "image": "",
        "barcode": "8901063173017"
    },

    "dairy_milk": {
        "name": "Dairy Milk",
        "category": "Chocolate",
        "sugar": 57,
        "sodium": 129,
        "fat": 29,
        "protein": 7.9,
        "calories": 531,
        "image": "",
        "barcode": "7622210063465"
    },

    "kitkat": {
        "name": "KitKat",
        "category": "Chocolate",
        "sugar": 39.3,
        "sodium": 84.8,
        "fat": 23.4,
        "protein": 5.5,
        "calories": 469,
        "image": "",
        "barcode": "8901058899999"
    },

    "munch": {
        "name": "Munch",
        "category": "Chocolate",
        "sugar": 45.1,
        "sodium": 103,
        "fat": 25.2,
        "protein": 4.7,
        "calories": 513,
        "image": "",
        "barcode": "8901058843323"
    },

    "perk": {
        "name": "Perk",
        "category": "Chocolate",
        "sugar": 39.3,
        "sodium": 84.8,
        "fat": 23.4,
        "protein": 5.5,
        "calories": 469,
        "image": "",
        "barcode": "7622201758660"
    },

    "5star": {
        "name": "5 Star",
        "category": "Chocolate",
        "sugar": 39.3,
        "sodium": 84.8,
        "fat": 23.4,
        "protein": 5.5,
        "calories": 469,
        "image": "",
        "barcode": "7622210622211"
    },

    "kellogs_muesli": {
        "name": "Kellogs Muesli",
        "category": "Healthy Food",
        "sugar": 10.7,
        "sodium": 132,
        "fat": 5.2,
        "protein": 9.3,
        "calories": 382,
        "image": "",
        "barcode": "5053827182447"
    },

    "quaker_oats": {
        "name": "Quaker Oats",
        "category": "Healthy Food",
        "sugar": 1,
        "sodium": 2,
        "fat": 7,
        "protein": 13,
        "calories": 389,
        "image": "",
        "barcode": "5000108022152"
    },

    "peanut_butter": {
        "name": "Sunfeast Peanut Butter",
        "category": "Healthy Spread",
        "sugar": 8.9,
        "sodium": 310,
        "fat": 52.4,
        "protein": 25,
        "calories": 637,
        "image": "",
        "barcode": "8901512881106"
    },

    "amul_milk": {
        "name": "Amul Milk",
        "category": "Dairy",
        "sugar": 5,
        "sodium": 150,
        "fat": 3,
        "protein": 3.5,
        "calories": 35,
        "image": "",
        "barcode": "8901262150064"
    },

    "yippee": {
        "name": "Yippee Noodles",
        "category": "Instant Food",
        "sugar": 5.7,
        "sodium": 300,
        "fat": 21.14,
        "protein": 8.2,
        "calories": 474,
        "image": "",
        "barcode": "8901014003181"
    },

    "maggi": {
        "name": "Maggi",
        "category": "Instant Food",
        "sugar": 1.8,
        "sodium": 1000,
        "fat": 12.5,
        "protein": 8.2,
        "calories": 384,
        "image": "",
        "barcode": "8901058000336"
    }
}
# ---------------- FETCH API ---------------- #

def fetch_product(barcode):
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"

        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5
        )

        if response.status_code != 200:
            return None

        data = response.json()

        if data.get("status") == 0:
            return None

        product = data.get("product", {})
        nutriments = product.get("nutriments", {})

        return {
            "name": product.get("product_name", "Unknown"),
            "sugar": float(nutriments.get("sugars_100g", 0)),
            "sodium": float(nutriments.get("sodium_100g", 0)) * 1000,
            "fat": float(nutriments.get("fat_100g", 0)),
            "protein": float(nutriments.get("proteins_100g", 0)),
            "calories": float(nutriments.get("energy-kcal_100g", 0)),
            "image": product.get("image_front_url") or product.get("image_url"),
            "data_source": "api"
        }

    except:
        return None

# ---------------- ROUTES ---------------- #
@app.route('/analyze')
def analyze():
    barcode = request.args.get('barcode')
    name = request.args.get('name')

    data = None

    # 1️⃣ Search in LOCAL DB using barcode
    if barcode:
        for value in INDIAN_PRODUCTS.values():
            if value.get("barcode") == barcode:
                data = value
                break

    # 2️⃣ Fallback to API
    if not data and barcode:
        data = fetch_product(barcode)

    # 3️⃣ Search by name
    if not data and name:
        name_lower = name.lower()
        for key, value in INDIAN_PRODUCTS.items():
            if key in name_lower or name_lower in key:
                data = value
                break

    # 4️⃣ Not found
    if not data:
        return jsonify({"error": "Product not found"})

    score = calculate_score(data["sugar"], data["sodium"], data["fat"])

    response = OrderedDict()
    response["food_name"] = data["name"]
    response["image"] = data.get("image", "")
    response["category_type"] = data.get("category", "Unknown")

    response["sugar"] = round(data["sugar"], 2)
    response["sodium"] = round(data["sodium"], 2)
    response["protein"] = round(data["protein"], 2)
    response["calories"] = round(data["calories"], 2)
    response["fat"] = round(data["fat"], 2)
    response["health_score"] = score
    response["category"] = get_category(score)
    response["verdict"] = get_verdict(score)
    response["color"] = get_color(score)
    response["alerts"] = get_alerts(data["sugar"], data["sodium"])
    response["daily_intake"] = get_daily_limits(data["sugar"], data["sodium"])
    response["healthy_alternatives"] = suggest_alternatives(
        data["name"], data["sugar"], data["sodium"], data["fat"], data.get("category", "")
    )
    response["data_source"] = data.get("data_source", "local")

    save_to_history(data, score, response["category"], response["verdict"])

    return jsonify(response)

# ---------------- RUN ---------------- #

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
