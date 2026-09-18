"""
Unified Integration: Voice Ordering + Food Image Recognition + Smart Recommendations
For AI Smart Food Delivery System - ICST University Park

This module orchestrates:
1. Voice ordering (multilingual chatbot)
2. Food image recognition + spoilage detection
3. Smart recommendations based on campus menu data
4. Real-time demand prediction
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

# Import all AI components
from voice_recognition import chat_loop, load_menu, build_item_index
from food_image_recognizer import recognize_food_hybrid
from spoilage_detector import SpoilageDetector, SimpleSpoilageClassifier
from recipe_lookup import RecipeLookup, LocalIngredientDatabase
from menu_recommender import load_menu as load_menu_model, build_feature_matrix
from food_ai_config import MENU_CSV_PATH


class SmartFoodDeliverySystem:
    """
    Unified system for campus food delivery with:
    - Voice ordering chatbot
    - Food image recognition
    - AI recommendations
    - Demand prediction
    """
    
    def __init__(self, campus_name: str = "ICST University Park"):
        self.campus_name = campus_name
        self.menu_data = None
        self.item_index = None
        self.spoilage_detector = None
        self.recipe_lookup = None
        self.user_profile = {}
        
        print(f"🏢 Initializing {campus_name} Food Delivery System")
        self._initialize_components()
    
    def _initialize_components(self):
        """Load all AI models and data"""
        print("⚙️  Loading components...")
        
        # Load campus menu
        self.menu_data = load_menu()
        self.item_index = build_item_index(self.menu_data)
        print(f"✓ Loaded {len(self.menu_data)} menu items")
        
        # Initialize spoilage detection
        self.spoilage_detector = SpoilageDetector(device='cpu')
        print("✓ Spoilage detector ready")
        
        # Initialize recipe lookup
        self.recipe_lookup = RecipeLookup()
        print("✓ Recipe lookup ready")
    
    def voice_order(self, language: str = 'en-US', mode: str = 'text') -> Dict:
        """
        Start voice/text ordering interface
        
        Args:
            language: Language for chat ('en-US', 'ta-IN', 'si-LK', etc.)
            mode: 'voice' (microphone) or 'text' (keyboard)
            
        Returns:
            Order details
        """
        print(f"\n🎤 Starting {language} Voice Ordering...")
        
        # Run chat loop
        chat_loop(
            menu_items=self.menu_data,
            item_index=self.item_index,
            lang=language,
            recognizer=None,
            microphone=None,
            backend='google'
        )
        
        return {'status': 'order_placed', 'language': language}
    
    def analyze_food_image(self, image_path: str, 
                          check_spoilage: bool = True) -> Dict:
        """
        Analyze food image for:
        - Food identification
        - Spoilage status
        - Recipe/ingredients
        - Menu matching
        
        Args:
            image_path: Path to food image
            check_spoilage: Whether to run spoilage detection
            
        Returns:
            Combined analysis results
        """
        results = {
            'image': image_path,
            'food_recognized': None,
            'spoilage_status': None,
            'matched_menu_items': [],
            'recommendation': None,
        }
        
        print(f"\n📸 Analyzing food image: {image_path}")
        print("=" * 60)
        
        # Step 1: Food Recognition
        print("🔍 Recognizing food...")
        recognition = recognize_food_hybrid(image_path, use_local=False)
        food_items = recognition.get('merged', {}).get('food_items', [])
        results['food_recognized'] = food_items
        
        if food_items:
            print(f"✓ Detected: {', '.join(food_items)}")
            
            # Step 2: Match to campus menu
            matched = self._match_to_menu(food_items)
            results['matched_menu_items'] = matched
            
            if matched:
                print(f"✓ Found on menu: {[m['name'] for m in matched]}")
        
        # Step 3: Spoilage Check
        if check_spoilage:
            print("🧪 Checking freshness...")
            spoilage_result = self.spoilage_detector.infer(image_path)
            
            if spoilage_result.get('success'):
                results['spoilage_status'] = spoilage_result.get('status')
                confidence = spoilage_result.get('confidence', 0)
                print(f"✓ Status: {spoilage_result['status']} ({confidence*100:.1f}%)")
            else:
                simple = SimpleSpoilageClassifier()
                fallback = simple.infer_simple(image_path)
                results['spoilage_status'] = fallback.get('status')
                print(f"⚠ Fallback analysis: {fallback.get('status')}")
        
        # Step 4: Get recommendation
        if matched:
            results['recommendation'] = self._get_recommendation(matched[0])
        
        return results
    
    def _match_to_menu(self, food_names: List[str]) -> List[Dict]:
        """Match recognized food to campus menu"""
        matched = []
        
        for food_name in food_names:
            # Check exact or partial match
            for item in self.menu_data:
                if food_name.lower() in item['name'].lower() or \
                   item['name'].lower() in food_name.lower():
                    matched.append(item)
                    break
        
        return matched
    
    def _get_recommendation(self, menu_item: Dict) -> Dict:
        """Get smart recommendation based on item"""
        recommendation = {
            'item': menu_item['name'],
            'price': menu_item['price'],
            'category': menu_item.get('category', 'Unknown'),
            'complementary': [],
            'dietary_note': 'Vegetarian' if menu_item.get('veg') else 'Non-vegetarian',
        }
        
        # Find complementary items
        item_price = menu_item['price']
        item_category = menu_item.get('category')
        
        for candidate in self.menu_data:
            # Suggest different category at similar price
            if candidate['name'] != menu_item['name'] and \
               candidate.get('category') != item_category and \
               abs(candidate['price'] - item_price) < 100:
                recommendation['complementary'].append({
                    'name': candidate['name'],
                    'price': candidate['price'],
                    'reason': f"Complements {item_category}"
                })
                if len(recommendation['complementary']) >= 3:
                    break
        
        return recommendation
    
    def create_order(self, items: List[str], user_id: str = "anon", 
                    special_requests: str = "") -> Dict:
        """
        Create an order
        
        Args:
            items: List of item names to order
            user_id: Student/staff ID
            special_requests: Special instructions
            
        Returns:
            Order confirmation
        """
        order = {
            'order_id': f"ORD_{user_id}_{len(items)}",
            'timestamp': str(pd.Timestamp.now()),
            'user_id': user_id,
            'items': [],
            'total_price': 0,
            'special_requests': special_requests,
            'estimated_ready_time': None,
            'delivery_location': 'Campus (TBD)',
        }
        
        # Build order
        prep_time = 0
        for item_name in items:
            matched = None
            for menu_item in self.menu_data:
                if item_name.lower() in menu_item['name'].lower():
                    matched = menu_item
                    break
            
            if matched:
                order['items'].append({
                    'name': matched['name'],
                    'price': matched['price'],
                    'category': matched.get('category'),
                })
                order['total_price'] += matched['price']
                prep_time += 180  # 3 min per item
        
        # Estimate delivery time
        order['estimated_ready_time'] = f"{prep_time // 60} mins"
        
        print(f"\n✓ Order created: {order['order_id']}")
        print(f"  Total: Rs. {order['total_price']}")
        print(f"  Ready in: {order['estimated_ready_time']}")
        
        return order
    
    def get_demand_forecast(self, hour: int = None) -> Dict:
        """
        Predict demand for next hour
        Uses campus schedule + historical patterns
        """
        import datetime
        
        if hour is None:
            hour = datetime.datetime.now().hour
        
        # Simple heuristic based on campus schedule
        # Peak hours: 8-9 AM (breakfast), 12-2 PM (lunch), 5-8 PM (dinner)
        peak_hours = {
            8: 0.9,   # High breakfast demand
            9: 0.8,
            12: 1.0,  # Peak lunch
            13: 0.95,
            14: 0.7,
            17: 0.8,  # Early dinner
            18: 0.9,
            19: 0.85,
        }
        
        demand_level = peak_hours.get(hour, 0.4)
        
        forecast = {
            'hour': hour,
            'demand_level': demand_level,
            'forecast_text': {
                0.9: 'Very High',
                0.8: 'High',
                0.7: 'Medium-High',
                0.5: 'Medium',
            }.get(round(demand_level, 1), 'Low'),
            'recommended_prep': 'Prepare larger batches' if demand_level > 0.7 else 'Standard prep',
        }
        
        # Recommend popular items
        if 8 <= hour < 11:
            forecast['popular_category'] = 'Breakfast'
        elif 11 <= hour < 15:
            forecast['popular_category'] = 'Lunch'
        elif hour >= 17:
            forecast['popular_category'] = 'Dinner'
        else:
            forecast['popular_category'] = 'Snacks & Beverages'
        
        return forecast
    
    def get_system_status(self) -> Dict:
        """Get overall system status"""
        return {
            'system': self.campus_name,
            'status': 'operational',
            'components': {
                'voice_chatbot': 'ready',
                'image_recognition': 'ready',
                'spoilage_detector': 'ready',
                'recommendation_engine': 'ready',
                'menu_items_loaded': len(self.menu_data),
            },
            'campus_menu': {
                'total_items': len(self.menu_data),
                'categories': list(set(item.get('category') for item in self.menu_data)),
                'vegetarian_count': sum(1 for item in self.menu_data if item.get('veg')),
            },
        }


# Example usage
if __name__ == '__main__':
    # Initialize system
    system = SmartFoodDeliverySystem("ICST University Park")
    
    # Show status
    print("\n" + "=" * 60)
    print(system.get_system_status())
    print("=" * 60)
    
    # Example 1: Show current demand forecast
    print("\n📊 Demand Forecast (Next 3 Hours):")
    import datetime
    for i in range(3):
        hour = (datetime.datetime.now().hour + i) % 24
        forecast = system.get_demand_forecast(hour)
        print(f"  {hour:02d}:00 → {forecast['forecast_text']} ({forecast.get('popular_category', 'N/A')})")
    
    print("\n✓ System initialized and ready!")
    print("Use: system.voice_order(), system.analyze_food_image(), system.create_order()")
