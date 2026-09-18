"""
Spoonacular API integration helper
"""
import os
import requests
from typing import Dict, List

API_KEY = os.getenv('SPOONACULAR_API_KEY', '')
BASE = 'https://api.spoonacular.com'


def search_recipes_spoonacular(query: str, number: int = 5) -> Dict:
    if not API_KEY:
        return {'success': False, 'error': 'No Spoonacular API key configured'}

    try:
        params = {
            'query': query,
            'number': number,
            'apiKey': API_KEY,
        }
        r = requests.get(f"{BASE}/recipes/complexSearch", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = []
        for item in data.get('results', [])[:number]:
            results.append({
                'id': item.get('id'),
                'title': item.get('title'),
            })
        return {'success': True, 'recipes': results}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_recipe_information(recipe_id: int) -> Dict:
    if not API_KEY:
        return {'success': False, 'error': 'No Spoonacular API key configured'}

    try:
        params = {'apiKey': API_KEY, 'includeNutrition': True}
        r = requests.get(f"{BASE}/recipes/{recipe_id}/information", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        ingredients = [ing.get('originalString') for ing in data.get('extendedIngredients', [])]
        return {
            'success': True,
            'title': data.get('title'),
            'ingredients': ingredients,
            'servings': data.get('servings'),
            'readyInMinutes': data.get('readyInMinutes'),
            'sourceUrl': data.get('sourceUrl'),
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
