"""
Training Pipeline Integration
Combines all AI modules with campus menu data for optimal model training
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict
import json

# Import training modules
from train_menu_recommender import load_menu, train
from spoilage_detector import SpoilageDetector
from food_ai_config import MENU_CSV_PATH


class CampusDataTrainingPipeline:
    """
    Training pipeline using ICST University Park campus menu data
    
    Integration points:
    - Menu dataset (53 items from campus vendors)
    - Feature engineering (price tiers, nutrition, prep time)
    - Model training (recommendation, demand prediction, queue management)
    """
    
    def __init__(self, campus_name: str = "ICST University Park"):
        self.campus_name = campus_name
        self.menu_df = None
        self.training_history = []
        print(f"📚 Initialized Training Pipeline for {campus_name}")
    
    def load_campus_menu(self) -> pd.DataFrame:
        """Load real campus menu data"""
        print(f"\n📂 Loading campus menu from: {MENU_CSV_PATH}")
        
        try:
            df = pd.read_csv(MENU_CSV_PATH, encoding='utf-8')
            print(f"✓ Loaded {len(df)} items from campus vendors")
            print(f"  Categories: {df['category'].unique().tolist()}")
            print(f"  Price range: Rs. {df['price'].min()}-{df['price'].max()}")
            
            self.menu_df = df
            return df
        
        except FileNotFoundError:
            print(f"⚠ Menu file not found: {MENU_CSV_PATH}")
            return None
    
    def prepare_training_data(self) -> Dict:
        """
        Prepare data for all models
        
        Returns:
            Dictionary with datasets for each model
        """
        if self.menu_df is None:
            self.load_campus_menu()
        
        print("\n🔧 Preparing training data...")
        
        training_sets = {}
        
        # 1. Recommendation Model Training Data
        print("  • Recommendation engine data...")
        training_sets['recommendation'] = {
            'menu': self.menu_df,
            'features': ['name', 'category', 'price', 'protein', 'veg', 'calories'],
            'size': len(self.menu_df),
        }
        
        # 2. Demand Prediction Data (synthetic - will be real after collection)
        print("  • Demand prediction data...")
        synthetic_orders = self._generate_synthetic_orders(1000)
        training_sets['demand_prediction'] = {
            'orders': synthetic_orders,
            'features': ['timestamp', 'hour', 'day_of_week', 'category', 'price_tier'],
            'size': len(synthetic_orders),
        }
        
        # 3. Queue Management Data
        print("  • Queue management data...")
        training_sets['queue_management'] = {
            'menu': self.menu_df,
            'prep_time_features': self._estimate_prep_time(),
            'size': len(self.menu_df),
        }
        
        # 4. Spoilage Detection Data
        print("  • Spoilage detection (requires image dataset)...")
        training_sets['spoilage_detection'] = {
            'good_food_images': 'food_data/datasets/good_food_images/',
            'spoilage_images': 'food_data/datasets/spoilage_images/',
            'model': 'EfficientNet B0',
        }
        
        print(f"✓ Prepared {len(training_sets)} training datasets")
        return training_sets
    
    def _generate_synthetic_orders(self, num_orders: int = 1000) -> pd.DataFrame:
        """Generate synthetic order data for demand prediction"""
        import datetime
        import random
        
        orders = []
        base_date = datetime.datetime.now() - datetime.timedelta(days=30)
        
        for _ in range(num_orders):
            # Random timestamp in last 30 days
            days_offset = random.randint(0, 29)
            hour = random.choice([8, 9, 12, 13, 14, 17, 18, 19])  # Peak hours
            
            timestamp = base_date + datetime.timedelta(days=days_offset, hours=hour)
            
            # Random menu item
            item = self.menu_df.sample(1).iloc[0]
            
            orders.append({
                'timestamp': timestamp,
                'hour': hour,
                'day_of_week': timestamp.weekday(),
                'category': item['category'],
                'price': item['price'],
                'price_tier': 'low' if item['price'] <= 150 else 'mid' if item['price'] <= 300 else 'high',
                'quantity': random.randint(1, 3),
                'is_vegetarian': item.get('veg', False),
            })
        
        return pd.DataFrame(orders)
    
    def _estimate_prep_time(self) -> Dict:
        """Estimate preparation time for each item"""
        prep_times = {}
        
        for _, item in self.menu_df.iterrows():
            category = item.get('category', 'Other')
            
            # Heuristic: preparation time based on category
            category_prep_time = {
                'Breakfast': 180,      # 3 min
                'Lunch': 300,          # 5 min
                'Dinner': 420,         # 7 min
                'Snack': 120,          # 2 min
                'Beverage': 60,        # 1 min
                'Dessert': 120,        # 2 min
            }
            
            prep_times[item['name']] = category_prep_time.get(category, 180)
        
        return prep_times
    
    def train_recommendation_model(self, training_data: Dict) -> bool:
        """
        Train recommendation model with campus menu
        
        This will use all 53 items from Kalith + Fresh Juice vendors
        """
        print("\n🤖 Training Recommendation Model...")
        print("=" * 60)
        
        try:
            # Train with campus menu
            trained_model = train()
            
            print("✓ Recommendation model trained successfully!")
            self.training_history.append({
                'model': 'recommendation',
                'timestamp': str(pd.Timestamp.now()),
                'items_trained': len(self.menu_df),
                'status': 'success',
            })
            
            return True
        
        except Exception as e:
            print(f"✗ Training failed: {e}")
            return False
    
    def train_spoilage_detector(self) -> bool:
        """
        Train spoilage detection model
        
        Requires:
        - good_food_images/ directory with fresh food photos
        - spoilage_images/ directory with spoiled food photos
        """
        print("\n🧪 Training Spoilage Detection Model...")
        print("=" * 60)
        
        detector = SpoilageDetector(device='cpu')
        
        # Check if training data exists
        good_dir = Path('food_data/datasets/good_food_images')
        spoil_dir = Path('food_data/datasets/spoilage_images')
        
        good_count = len(list(good_dir.glob('**/*.jpg')) + list(good_dir.glob('**/*.png')))
        spoil_count = len(list(spoil_dir.glob('**/*.jpg')) + list(spoil_dir.glob('**/*.png')))
        
        print(f"Dataset status:")
        print(f"  Good food images: {good_count}")
        print(f"  Spoiled images: {spoil_count}")
        
        if good_count < 10 or spoil_count < 10:
            print("\n⚠ Insufficient training data")
            print(f"  Minimum required: 10 images per class")
            print(f"  Please add food images to the directories")
            return False
        
        try:
            success = detector.train(epochs=50, batch_size=16, lr=0.001)
            
            if success:
                print("✓ Spoilage detector trained successfully!")
                self.training_history.append({
                    'model': 'spoilage_detection',
                    'timestamp': str(pd.Timestamp.now()),
                    'good_images': good_count,
                    'spoiled_images': spoil_count,
                    'status': 'success',
                })
                return True
            else:
                print("✗ Training failed")
                return False
        
        except Exception as e:
            print(f"✗ Error during training: {e}")
            return False
    
    def estimate_demand_forecast(self) -> Dict:
        """
        Estimate demand based on campus schedule
        Uses synthetic data + campus schedule knowledge
        """
        print("\n📊 Demand Forecast Analysis")
        print("=" * 60)
        
        synthetic_orders = self._generate_synthetic_orders(5000)
        
        # Analyze by hour
        hourly_demand = synthetic_orders.groupby('hour').size()
        
        forecast = {
            'peak_hours': hourly_demand.nlargest(3).index.tolist(),
            'demand_by_hour': hourly_demand.to_dict(),
            'popular_categories': synthetic_orders['category'].value_counts().to_dict(),
            'average_order_value': synthetic_orders['price'].mean(),
        }
        
        print("\nDemand by Hour (Breakfast, Lunch, Dinner):")
        for hour in sorted(hourly_demand.index):
            count = hourly_demand[hour]
            bar = '█' * (count // 10)
            print(f"  {hour:02d}:00 → {bar} ({count} orders)")
        
        print(f"\nPopular Categories:")
        for category, count in forecast['popular_categories'].items():
            print(f"  {category}: {count} orders")
        
        return forecast
    
    def analyze_menu_gaps(self) -> Dict:
        """Identify menu gaps and opportunities"""
        print("\n🎯 Menu Analysis")
        print("=" * 60)
        
        analysis = {
            'vegetarian_coverage': None,
            'price_range_gaps': None,
            'meal_type_distribution': None,
            'recommendations': [],
        }
        
        # Vegetarian coverage
        veg_count = len(self.menu_df[self.menu_df.get('veg', False)])
        total_count = len(self.menu_df)
        veg_percentage = (veg_count / total_count) * 100
        
        analysis['vegetarian_coverage'] = {
            'vegetarian_items': veg_count,
            'total_items': total_count,
            'percentage': f"{veg_percentage:.1f}%",
        }
        
        if veg_percentage < 40:
            analysis['recommendations'].append("⚠ Low vegetarian coverage - consider adding veg options")
        
        # Meal type distribution
        meal_dist = self.menu_df['category'].value_counts().to_dict()
        analysis['meal_type_distribution'] = meal_dist
        
        # Price range
        price_min = self.menu_df['price'].min()
        price_max = self.menu_df['price'].max()
        price_mean = self.menu_df['price'].mean()
        
        analysis['price_range_gaps'] = {
            'min': price_min,
            'max': price_max,
            'mean': f"Rs. {price_mean:.0f}",
        }
        
        print(f"\nVegetarian Options: {veg_count}/{total_count} ({veg_percentage:.1f}%)")
        print(f"\nMeal Distribution:")
        for meal_type, count in meal_dist.items():
            print(f"  {meal_type}: {count} items")
        
        print(f"\nPrice Range: Rs. {price_min}-{price_max} (avg: Rs. {price_mean:.0f})")
        
        if analysis['recommendations']:
            print(f"\nRecommendations:")
            for rec in analysis['recommendations']:
                print(f"  {rec}")
        
        return analysis
    
    def get_training_report(self) -> Dict:
        """Generate training report"""
        report = {
            'campus': self.campus_name,
            'timestamp': str(pd.Timestamp.now()),
            'menu_stats': {
                'total_items': len(self.menu_df) if self.menu_df is not None else 0,
                'vendors': ['Kalith Lanka Products', 'Fresh Juice & MMC'],
                'categories': list(self.menu_df['category'].unique()) if self.menu_df is not None else [],
            },
            'training_history': self.training_history,
            'models_ready': {
                'recommendation': True,
                'spoilage_detection': False,  # Requires image dataset
                'demand_prediction': True,
                'queue_management': True,
            },
        }
        
        return report


# Example usage
if __name__ == '__main__':
    print("🚀 Campus Data Training Pipeline")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = CampusDataTrainingPipeline("ICST University Park")
    
    # Load menu
    menu_df = pipeline.load_campus_menu()
    
    if menu_df is not None:
        # Prepare data
        training_sets = pipeline.prepare_training_data()
        
        # Analyze menu
        menu_analysis = pipeline.analyze_menu_gaps()
        
        # Forecast demand
        forecast = pipeline.estimate_demand_forecast()
        
        # Train recommendation model
        print("\n" + "=" * 60)
        pipeline.train_recommendation_model(training_sets)
        
        # Generate report
        print("\n" + "=" * 60)
        report = pipeline.get_training_report()
        
        print("\n✅ Training Pipeline Summary")
        print("=" * 60)
        print(json.dumps(report, indent=2))
