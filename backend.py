from flask import Flask, request, jsonify
import requests
from collections import OrderedDict
import sqlite3
from datetime import datetime
import os

app = Flask(**name**)
app.json.sort_keys = False

# ---------------- DATABASE ----------------

DB_NAME = "history.db"

def init_db():
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

```
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
```

init_db()

def save_to_history(data, score, category, verdict):
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

```
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
```

# ---------------- HEALTH LOGIC ----------------

def calculate_score(sugar, sodium, fat):
score = 10

```
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
```

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

# ---------------- ALERTS ----------------

def get_alerts(sugar, sodium):
alerts = []

```
if sugar > 40:
    alerts.append("⚠️ Extremely high sugar – Avoid completely")
elif sugar > 15:
    alerts.append("⚠️ High sugar – Limit intake")

if sodium > 600:
    alerts.append("⚠️ Very high sodium – Risk for BP")
elif sodium > 300:
    alerts.append("⚠️ Moderate sodium – Be careful")

return alerts
```

# ---------------- DAILY LIMIT ----------------

def get_daily_limits(sugar, sodium):
return {
"sugar_%": min(round((sugar / 25) * 100, 2), 100),
"sodium_%": min(round((sodium / 2000) * 100, 2), 100)
}

# ---------------- ALTERNATIVES ----------------

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

def suggest_alternatives(name, sugar, sodium, fat):
name = name.lower()

```
for key in PRODUCT_ALTERNATIVES:
    if key in name:
        return PRODUCT_ALTERNATIVES[key]

suggestions = []

if "drink" in name:
    suggestions.extend(HEALTHY_ALTERNATIVES["drinks"])

if sugar > 15:
    suggestions.extend(HEALTHY_ALTERNATIVES["high_sugar"])
if sodium > 500:
    suggestions.extend(HEALTHY_ALTERNATIVES["high_sodium"])
if fat > 20:
    suggestions.extend(HEALTHY_ALTERNATIVES["high_fat"])

return list(set(suggestions))
```

# ---------------- LOCAL DATA ----------------

INDIAN_PRODUCTS = {
"p16_aloo_bhujia": {
"name": "Aloo Bhujia",
"category": "Snack",
"sugar": 0.25,
"sodium": 615,
"fat": 38.12,
"protein": 8.68,
"calories": 562,
"image": ""
},
"kurkure": {
"name": "Kurkure",
"sugar": 1.0,
"sodium": 892,
"fat": 34.6,
"protein": 6.4,
"calories": 558,
"image": "https://m.media-amazon.com/images/I/81z5Z6n6VxL.jpg"
},
"p4_pepsi": {
    "name": "Pepsi",
    "category": "Soft Drink",
    "sugar": 11.0,
    "sodium": 7,
    "fat": 0,
    "protein": 0,
    "calories": 42,
    "image": ""
},
"lays": {
"name": "Lays Chips",
"sugar": 1.2,
"sodium": 650,
"fat": 34.0,
"protein": 6.0,
"calories": 536,
"image": "https://m.media-amazon.com/images/I/61XzLZ5wFLL.jpg"
},
"p26_bingo": {
"name": "Bingo Chips",
"category": "Snack",
"sugar": 6,
"sodium": 758,
"fat": 29.5,
"protein": 5.6,
"calories": 526,
"image": ""
},
"p27_uncle_chips": {
"name": "Uncle Chips",
"category": "Snack",
"sugar": 0.6,
"sodium": 591,
"fat": 35,
"protein": 6.7,
"calories": 550,
"image": ""
},
"p28_doritos": {
"name": "Doritos",
"category": "Snack",
"sugar": 4.5,
"sodium": 605,
"fat": 23.4,
"protein": 7.1,
"calories": 499,
"image": ""
},
"p29_too_yumm": {
"name": "Too Yumm Chips",
"category": "Snack",
"sugar": 8.5,
"sodium": 880,
"fat": 18.3,
"protein": 7.9,
"calories": 464,
"image": ""
},

```
"p1_britannia_cake": {
    "name": "Britannia Little Roll Cake",
    "category": "Cake",
    "sugar": 30.2,
    "sodium": 252.6,
    "fat": 17.3,
    "protein": 5.7,
    "calories": 415,
    "image": ""
},

"p2_paper_boat": {
    "name": "Paper Boat Drink",
    "category": "Drink",
    "sugar": 13.0,
    "sodium": 40,
    "fat": 0,
    "protein": 0,
    "calories": 52.8,
    "image": ""
},

"p3_coca_cola": {
    "name": "Coca Cola",
    "category": "Soft Drink",
    "sugar": 10.6,
    "sodium": 8.5,
    "fat": 0,
    "protein": 0,
    "calories": 44,
    "image": ""
}
```

}

# ---------------- FETCH API ----------------

def fetch_product(barcode):
try:
url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"

```
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
```

# ---------------- ROUTES ----------------

@app.route('/analyze')
def analyze():
barcode = request.args.get('barcode')
name = request.args.get('name')

```
data = None

if barcode:
    data = fetch_product(barcode)

if not data and name:
    name_lower = name.lower()

    for key, value in INDIAN_PRODUCTS.items():
        product_name = value["name"].lower()

        if name_lower in product_name or product_name in name_lower:
            data = value
            break

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
    data["name"], data["sugar"], data["sodium"], data["fat"]
)
response["data_source"] = data.get("data_source", "local")

save_to_history(data, score, response["category"], response["verdict"])

return jsonify(response)
```

@app.route('/history')
def history():
conn = sqlite3.connect(DB_NAME)

```
cursor = conn.cursor()

cursor.execute("SELECT * FROM history ORDER BY id DESC")
rows = cursor.fetchall()
conn.close()

result = []
for row in rows:
    result.append({
        "id": row[0],
        "food_name": row[1],
        "health_score": row[7],
        "category": row[8],
        "verdict": row[9],
        "image": row[10],
        "timestamp": row[11]
    })

return jsonify(result)
```

# ---------------- RUN ----------------

if **name** == '**main**':
port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)
