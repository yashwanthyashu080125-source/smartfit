import requests
from app.config import Config

# =========================================
# FOOD DETECTION FROM IMAGE
# =========================================

def detect_food(image_path):

    url = "https://api.spoonacular.com/food/images/analyze"

    try:

        with open(image_path, "rb") as image_file:

            files = {
                "file": image_file
            }

            params = {
                "apiKey": Config.SPOONACULAR_API_KEY
            }

            response = requests.post(url, files=files, params=params)

        if response.status_code == 200:

            data = response.json()

            foods = []

            # Spoonacular returns category or possible foods
            if "category" in data and "name" in data["category"]:
                foods.append(data["category"]["name"])

            # fallback if other structure returned
            if "annotations" in data:
                for item in data["annotations"]:
                    foods.append(item.get("tag", ""))

            return foods

        else:
            print("Food detection API error:", response.status_code, response.text)

    except Exception as e:
        print("Food detection error:", e)

    return []


# =========================================
# GET FOOD NUTRITION FROM NAME
# =========================================

def get_food_nutrition(food_name):

    url = "https://api.spoonacular.com/recipes/guessNutrition"

    params = {
        "title": food_name,
        "apiKey": Config.SPOONACULAR_API_KEY
    }

    try:

        response = requests.get(url, params=params)

        if response.status_code == 200:

            data = response.json()

            # Ensure valid nutrition data
            if "calories" in data:
                return data
            else:
                print("Nutrition data missing:", data)

        else:
            print("Nutrition API error:", response.status_code, response.text)

    except Exception as e:
        print("Nutrition API exception:", e)

    return None