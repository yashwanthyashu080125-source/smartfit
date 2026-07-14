import requests
import os

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")


def recommend_meals(goal, workout_type):

    tags = []
    diet = None

    # Goal based logic
    if goal == "lose_weight":
        tags.append("low-carb")
        diet = "low-carb"

    elif goal == "gain_muscle":
        tags.append("high-protein")

    elif goal == "maintain":
        tags.append("balanced")

    # Workout type influence
    if workout_type == "cardio":
        tags.append("energy")

    if workout_type == "strength":
        tags.append("high-protein")

    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": 5,
        "tags": ",".join(tags)
    }

    response = requests.get(
        "https://api.spoonacular.com/recipes/random",
        params=params
    )

    data = response.json()

    meals = []

    for recipe in data.get("recipes", []):
        meals.append({
            "title": recipe["title"],
            "image": recipe["image"],
            "source": recipe["sourceUrl"]
        })

    return meals