import requests

# SPOONACULAR_API_KEY = 'd3c58935887b4ebf989738755f635e2e'
SPOONACULAR_API_KEY = '08798ac49dd8428586293dd129ec56df'
BASE_URL = 'https://api.spoonacular.com/recipes'

def get_recipes_by_ingredients(ingredients):
    """
    Fetch recipes from Spoonacular based on a list of ingredients.
    """
    url = f"{BASE_URL}/findByIngredients"
    params = {
        'apiKey': SPOONACULAR_API_KEY,
        'ingredients': ingredients,
        'number': 5
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        recipes = response.json()

        # Fetch details for each recipe
        detailed_recipes = []
        for recipe in recipes:
            recipe_id = recipe['id']
            recipe_details = get_recipe_details(recipe_id)
            detailed_recipes.append(recipe_details)

        return detailed_recipes
    else:
        print("API Error:", response.status_code, response.text)
        return []

def get_recipe_details(recipe_id):
    """
    Fetch detailed information about a specific recipe.
    """
    url = f"{BASE_URL}/{recipe_id}/information"
    params = {'apiKey': SPOONACULAR_API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        recipe = response.json()
        return {
            "id": recipe["id"],
            "title": recipe["title"],
            "image": recipe["image"],
            "ingredients": recipe["extendedIngredients"],
            "instructions": recipe["instructions"],
            "sourceUrl": recipe["sourceUrl"],
        }
    else:
        print(f"Error fetching details for recipe {recipe_id}")
        return None