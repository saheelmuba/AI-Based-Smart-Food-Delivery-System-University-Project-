"""
Recipe and Ingredient Lookup
Integrates Edamam Recipe API for ingredient and nutrition information
"""
from typing import Dict, List, Optional
import requests
from urllib.parse import quote
import pandas as pd
from pathlib import Path

from food_ai_config import (
    EDAMAM_APP_ID,
    EDAMAM_API_KEY,
    MENU_CSV_PATH,
    ENDPOINTS,
)
from spoonacular_lookup import search_recipes_spoonacular, get_recipe_information


class RecipeLookup:
    """Lookup recipes and ingredients using Edamam API"""
    
    def __init__(self):
        self.app_id = EDAMAM_APP_ID
        self.api_key = EDAMAM_API_KEY
        self.recipe_endpoint = ENDPOINTS['edamam_recipe']
        self.nutrition_endpoint = ENDPOINTS['edamam_nutrition']
        self.menu_cache = self._load_menu_cache()
    
    def _load_menu_cache(self) -> Dict:
        """Load menu items from local CSV for quick lookup"""
        cache = {}
        if MENU_CSV_PATH.exists():
            try:
                df = pd.read_csv(MENU_CSV_PATH, encoding='utf-8')
                for _, row in df.iterrows():
                    name = str(row.get('name', '')).lower()
                    cache[name] = {
                        'name': row.get('name'),
                        'price': row.get('price'),
                        'category': row.get('category'),
                        'protein': row.get('protein'),
                        'calories': row.get('calories'),
                        'veg': row.get('veg'),
                    }
            except Exception as e:
                print(f"Error loading menu cache: {e}")
        
        return cache
    
    def search_recipes(self, food_name: str, diet: Optional[str] = None, 
                      cuisine: Optional[str] = None) -> Dict:
        """
        Search for recipes using Edamam API
        
        Args:
            food_name: Name of the food item
            diet: Optional diet type (e.g., 'vegan', 'paleo')
            cuisine: Optional cuisine type (e.g., 'indian', 'asian')
            
        Returns:
            Dictionary with recipe results
        """
        # Prefer Spoonacular if configured
        try:
            from spoonacular_lookup import API_KEY as SP_KEY
        except Exception:
            SP_KEY = ''

        if SP_KEY:
            sp = search_recipes_spoonacular(food_name, number=5)
            if sp.get('success') and sp.get('recipes'):
                # fetch details for each
                recipes = []
                for r in sp.get('recipes', [])[:5]:
                    info = get_recipe_information(r.get('id'))
                    if info.get('success'):
                        recipes.append({
                            'label': info.get('title'),
                            'ingredients': info.get('ingredients'),
                            'source': info.get('sourceUrl'),
                            'yield': info.get('servings'),
                            'totalTime': info.get('readyInMinutes'),
                            'url': info.get('sourceUrl'),
                        })

                return {
                    'food_name': food_name,
                    'recipes_found': len(recipes),
                    'recipes': recipes,
                    'success': True,
                }

        if not self.app_id or not self.api_key:
            print("Warning: Edamam API credentials not configured")
            return self._get_local_recipe(food_name)
        
        try:
            params = {
                'type': 'public',
                'q': food_name,
                'app_id': self.app_id,
                'app_key': self.api_key,
            }
            
            if diet:
                params['diet'] = diet
            if cuisine:
                params['cuisineType'] = cuisine
            
            response = requests.get(self.recipe_endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            recipes = data.get('hits', [])
            
            results = {
                'food_name': food_name,
                'recipes_found': len(recipes),
                'recipes': [],
            }
            
            for hit in recipes[:5]:  # Top 5 recipes
                recipe = hit.get('recipe', {})
                results['recipes'].append({
                    'label': recipe.get('label'),
                    'uri': recipe.get('uri'),
                    'ingredients': recipe.get('ingredientLines', []),
                    'source': recipe.get('source'),
                    'yield': recipe.get('yield'),
                    'cuisine_type': recipe.get('cuisineType', []),
                    'diet_labels': recipe.get('dietLabels', []),
                    'health_labels': recipe.get('healthLabels', []),
                    'total_time': recipe.get('totalTime'),
                    'calories': recipe.get('calories'),
                    'url': recipe.get('url'),
                })
            
            results['success'] = True
            return results
        
        except requests.exceptions.RequestException as e:
            print(f"API error: {e}")
            return self._get_local_recipe(food_name)
    
    def get_nutrition_info(self, ingredients: List[str]) -> Dict:
        """
        Get nutrition information for ingredients
        
        Args:
            ingredients: List of ingredient names
            
        Returns:
            Nutrition data
        """
        if not self.app_id or not self.api_key:
            return {
                'success': False,
                'error': 'Edamam API credentials not configured',
                'nutrition': None,
            }
        
        try:
            ingredient_text = '\n'.join(ingredients)
            params = {
                'app_id': self.app_id,
                'app_key': self.api_key,
            }
            
            response = requests.post(
                self.nutrition_endpoint,
                json={'ingredients': ingredients},
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'success': True,
                'ingredients': ingredients,
                'nutrition': {
                    'calories': data.get('calories'),
                    'protein': data.get('totalNutrients', {}).get('PROCNT', {}).get('quantity'),
                    'carbs': data.get('totalNutrients', {}).get('CHOCDF', {}).get('quantity'),
                    'fat': data.get('totalNutrients', {}).get('FAT', {}).get('quantity'),
                    'fiber': data.get('totalNutrients', {}).get('FIBTG', {}).get('quantity'),
                },
                'vitamin_info': self._extract_vitamins(data),
            }
        
        except Exception as e:
            print(f"Error getting nutrition info: {e}")
            return {
                'success': False,
                'error': str(e),
                'nutrition': None,
            }
    
    def _extract_vitamins(self, nutrition_data: Dict) -> Dict:
        """Extract vitamin and mineral information"""
        vitamins = {}
        nutrient_map = {
            'VITA_RAE': 'Vitamin A',
            'VITC': 'Vitamin C',
            'VITD': 'Vitamin D',
            'TOCPHA': 'Vitamin E',
            'VITK1': 'Vitamin K',
            'VITB12': 'Vitamin B12',
            'CA': 'Calcium',
            'FE': 'Iron',
            'MG': 'Magnesium',
        }
        
        for nutrient_id, display_name in nutrient_map.items():
            if nutrient_id in nutrition_data.get('totalNutrients', {}):
                nutrient = nutrition_data['totalNutrients'][nutrient_id]
                vitamins[display_name] = {
                    'quantity': nutrient.get('quantity'),
                    'unit': nutrient.get('unit'),
                }
        
        return vitamins
    
    def _get_local_recipe(self, food_name: str) -> Dict:
        """Fallback: get recipe from local menu cache"""
        food_key = food_name.lower()
        
        if food_key in self.menu_cache:
            item = self.menu_cache[food_key]
            return {
                'success': True,
                'source': 'local_menu',
                'food_name': food_name,
                'item_info': item,
                'recipes': [],
            }
        
        return {
            'success': False,
            'source': 'local_menu',
            'error': f'Food "{food_name}" not found in local menu',
            'recipes': [],
        }
    
    def get_ingredients_for_food(self, food_name: str) -> Dict:
        """
        Get ingredients needed to prepare a food item
        
        Args:
            food_name: Name of the food
            
        Returns:
            Dictionary with ingredients and preparation info
        """
        recipes = self.search_recipes(food_name)
        
        if not recipes.get('recipes'):
            return {
                'food_name': food_name,
                'success': False,
                'ingredients': [],
                'error': 'No recipes found',
            }
        
        # Get top recipe
        top_recipe = recipes['recipes'][0]
        
        ingredients_formatted = []
        if top_recipe.get('ingredients'):
            ingredients_formatted = [
                {
                    'ingredient': ing,
                    'parsed': self._parse_ingredient(ing)
                }
                for ing in top_recipe['ingredients']
            ]
        
        return {
            'food_name': food_name,
            'recipe_name': top_recipe.get('label'),
            'success': True,
            'ingredients': ingredients_formatted,
            'total_time': top_recipe.get('total_time'),
            'servings': top_recipe.get('yield'),
            'source': top_recipe.get('source'),
            'url': top_recipe.get('url'),
        }
    
    def _parse_ingredient(self, ingredient_line: str) -> Dict:
        """Parse an ingredient line into structured format"""
        # Simple parsing: try to extract quantity, unit, and ingredient name
        parts = ingredient_line.strip().split()
        
        return {
            'raw': ingredient_line,
            'quantity': parts[0] if parts else '',
            'unit': parts[1] if len(parts) > 1 else '',
            'name': ' '.join(parts[2:]) if len(parts) > 2 else ' '.join(parts[1:]),
        }
    
    def get_alternatives(self, food_name: str) -> Dict:
        """Get food alternatives (substitutes)"""
        recipes = self.search_recipes(food_name)
        
        return {
            'original_food': food_name,
            'alternatives': [
                {
                    'name': recipe.get('label'),
                    'calories': recipe.get('calories'),
                    'cuisine': recipe.get('cuisine_type'),
                }
                for recipe in recipes.get('recipes', [])
            ],
        }


class LocalIngredientDatabase:
    """Simple local ingredient database for quick lookup"""
    
    # Common ingredients database
    INGREDIENTS_DB = {
        'chicken': {
            'protein': 31,  # g per 100g
            'fat': 3.6,
            'carbs': 0,
            'calories': 165,
        },
        'rice': {
            'protein': 2.7,
            'fat': 0.3,
            'carbs': 28,
            'calories': 130,
        },
        'curry': {
            'protein': 2,
            'fat': 3,
            'carbs': 4,
            'calories': 50,
        },
        'egg': {
            'protein': 13,
            'fat': 11,
            'carbs': 1.1,
            'calories': 155,
        },
        'bread': {
            'protein': 8.6,
            'fat': 1.7,
            'carbs': 50,
            'calories': 265,
        },
        'juice': {
            'protein': 1,
            'fat': 0.1,
            'carbs': 12,
            'calories': 50,
        },
    }
    
    @classmethod
    def get_nutrition(cls, ingredient_name: str) -> Optional[Dict]:
        """Get nutrition for an ingredient"""
        ingredient_key = ingredient_name.lower()
        return cls.INGREDIENTS_DB.get(ingredient_key)
    
    @classmethod
    def estimate_nutrition(cls, food_name: str, quantity: float = 100) -> Dict:
        """Estimate nutrition based on common ingredients"""
        food_key = food_name.lower()
        base_nutrition = cls.INGREDIENTS_DB.get(food_key)
        
        if not base_nutrition:
            return {'error': f'No nutrition data for {food_name}'}
        
        scaled = {k: v * (quantity / 100) for k, v in base_nutrition.items()}
        return scaled
