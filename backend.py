from flask import Flask, request, jsonify
import requests
from collections import OrderedDict

app = Flask(__name__)
app.json.sort_keys = False

# ---------------- HEALTH LOGIC ---------------- #

def calculate_score(sugar, sodium, fat):
    score = 10

    if sugar > 10:
        score -= 2
    if sugar > 20:
        score -= 3

    if sodium > 300:
        score -= 2
    if sodium > 600:
        score -= 3

    if fat > 20:
        score -= 2

    return max(score, 0)

def get_category(score):
    return "Safe" if score >= 7 else "Moderate" if score >= 4 else "Avoid"

# ---------------- PERSONALIZED ALERTS ---------------- #

def get_alerts(sugar, sodium, mode):
    alerts = []

    if mode == "diabetes":
        alerts.append("High sugar – Not recommended" if sugar > 15 else "Safe for Diabetes")

    elif mode == "bp":
        alerts.append("High sodium – Not recommended" if sodium > 500 else "Safe for BP")

    elif mode == "fitness":
        alerts.append("Check protein and fat for fitness goals")

    else:
        if sugar > 15:
            alerts.append("Not recommended for Diabetes")
        else:
            alerts.append("Safe for Diabetes (limit intake)")

        if sodium > 500:
            alerts.append("Not recommended for BP")
        else:
            alerts.append("Safe for BP (limit intake)")

    return alerts

# ---------------- DAILY LIMIT ---------------- #

def get_daily_limits(sugar, sodium):
    return {
        "sugar_%": round((sugar / 25) * 100, 2),
        "sodium_%": round((sodium / 2000) * 100, 2)
    }

# ---------------- LOCAL PRODUCTS ---------------- #

INDIAN_PRODUCTS = {
    "maggi": {"name": "Maggi Noodles", "sugar": 1.8, "sodium": 1000, "fat": 12.5, "protein": 8.2, "calories": 384},
    "lays": {"name": "Lays Chips", "sugar": 1.0, "sodium": 600, "fat": 35, "protein": 6, "calories": 536},
    "kurkure": {"name": "Kurkure", "sugar": 3.0, "sodium": 700, "fat": 30, "protein": 6, "calories": 520},
    "oreo": {"name": "Oreo", "sugar": 38, "sodium": 270, "fat": 20, "protein": 5, "calories": 520},
    "dairy milk": {"name": "Dairy Milk", "sugar": 56, "sodium": 80, "fat": 30, "protein": 7, "calories": 534}
}

# ---------------- FETCH API ---------------- #

def fetch_product(barcode):
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            return None

        data = response.json()

        if data.get('status') != 1:
            return None

        product = data.get('product', {})
        nutriments = product.get('nutriments', {})

        return {
            "name": product.get('product_name', 'Unknown'),
            "sugar": float(nutriments.get('sugars_100g', 0)),
            "sodium": float(nutriments.get('sodium_100g', 0)) * 1000,
            "fat": float(nutriments.get('fat_100g', 0)),
            "protein": float(nutriments.get('proteins_100g', 0)),
            "calories": float(nutriments.get('energy-kcal_100g', 0))
        }

    except Exception as e:
        print("API Error:", e)
        return None

# ---------------- ROUTE ---------------- #

@app.route('/analyze')
def analyze():

    barcode = request.args.get('barcode')
    name = request.args.get('name')
    mode = request.args.get('mode', 'general')

    data = None

    # 1️⃣ Try API
    if barcode:
        data = fetch_product(barcode)

    # 2️⃣ SMART SEARCH (FIXED 🔥)
    if not data and name:
        name_lower = name.lower()
        for key in INDIAN_PRODUCTS:
            if key in name_lower:
                data = INDIAN_PRODUCTS[key]
                break

    if not data:
        return jsonify({"error": "Product not found"})

    score = calculate_score(data["sugar"], data["sodium"], data["fat"])

    response = OrderedDict()
    response["food_name"] = data["name"]
    response["sugar"] = round(data["sugar"], 2)
    response["sodium"] = round(data["sodium"], 2)
    response["protein"] = round(data["protein"], 2)
    response["calories"] = round(data["calories"], 2)
    response["fat"] = round(data["fat"], 2)
    response["health_score"] = score
    response["category"] = get_category(score)

    # ✅ Personalized alerts
    response["alerts"] = get_alerts(data["sugar"], data["sodium"], mode)

    # ✅ Daily intake
    response["daily_intake"] = get_daily_limits(data["sugar"], data["sodium"])

    return jsonify(response)

# ---------------- RUN ---------------- #

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)