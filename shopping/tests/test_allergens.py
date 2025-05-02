from django.test import TestCase
from shopping.allergens import AllergenDetector, COMMON_ALLERGENS, DIETARY_PREFERENCES


class AllergenDetectorTests(TestCase):
    """Tests for the AllergenDetector class"""
    
    def setUp(self):
        # Sample product data for testing
        self.milk_product = {
            'name': 'Milk',
            'ingredients': 'Milk, Vitamin D',
            'allergens': ['milk']
        }
        
        self.cereal_product = {
            'name': 'Wheat Cereal',
            'ingredients': 'Whole grain wheat, sugar, salt',
            'allergens': ['gluten', 'wheat']
        }
        
        self.candy_product = {
            'name': 'Chocolate Bar',
            'ingredients': 'Sugar, cocoa butter, chocolate liquor, milk solids, soy lecithin, vanilla',
            'allergens': ['milk', 'soy']
        }
        
        self.unknown_product = {
            'name': 'Mystery Product',
            'ingredients': None,
            'allergens': None
        }
        
        self.vegetarian_product = {
            'name': 'Vegetable Soup',
            'ingredients': 'Water, carrots, potatoes, onions, vegetable stock, salt, spices',
            'allergens': ['celery']
        }
        
        self.non_vegetarian_product = {
            'name': 'Chicken Soup',
            'ingredients': 'Water, chicken, carrots, potatoes, chicken stock, salt, spices',
            'allergens': []
        }

    def test_detect_allergens_from_allergen_tags(self):
        """Test allergen detection from allergen tags"""
        detected = AllergenDetector.detect_allergens(self.milk_product)
        self.assertIn('dairy', detected)
        self.assertIn('milk', detected['dairy'])
        
        detected = AllergenDetector.detect_allergens(self.cereal_product)
        self.assertIn('gluten', detected)
        
    def test_detect_allergens_from_ingredients(self):
        """Test allergen detection from ingredients text"""
        # Create a product with allergens in ingredients but not in allergen tags
        product = {
            'name': 'Peanut Butter',
            'ingredients': 'Roasted peanuts, salt',
            'allergens': []  # Empty allergen tags
        }
        
        detected = AllergenDetector.detect_allergens(product)
        self.assertIn('peanuts', detected)
        
    def test_detect_multiple_allergens(self):
        """Test detection of multiple allergens in a product"""
        detected = AllergenDetector.detect_allergens(self.candy_product)
        self.assertIn('dairy', detected)
        self.assertIn('soy', detected)
        
    def test_handle_missing_data(self):
        """Test handling of products with missing allergen/ingredient data"""
        detected = AllergenDetector.detect_allergens(self.unknown_product)
        self.assertEqual(detected, {})
        
    def test_check_dietary_preferences_vegetarian(self):
        """Test checking vegetarian dietary preference"""
        # Vegetarian product should have no conflicts
        conflicts = AllergenDetector.check_dietary_preferences(self.vegetarian_product)
        self.assertNotIn('vegetarian', conflicts)
        
        # Non-vegetarian product should have conflicts
        conflicts = AllergenDetector.check_dietary_preferences(self.non_vegetarian_product)
        self.assertIn('vegetarian', conflicts)
        self.assertIn('chicken', conflicts['vegetarian'])
        
    def test_check_dietary_preferences_vegan(self):
        """Test checking vegan dietary preference"""
        # The milk product has dairy, which conflicts with vegan diet
        conflicts = AllergenDetector.check_dietary_preferences(self.milk_product)
        self.assertIn('vegan', conflicts)
        self.assertIn('milk', conflicts['vegan'])
        
    def test_check_dietary_preferences_multiple(self):
        """Test checking multiple dietary preferences"""
        # Create a product that conflicts with multiple diets
        product = {
            'name': 'Sugary Pork Product',
            'ingredients': 'Pork, sugar, salt, wheat flour'
        }
        
        conflicts = AllergenDetector.check_dietary_preferences(product)
        self.assertIn('vegan', conflicts)
        self.assertIn('vegetarian', conflicts)
        self.assertIn('halal', conflicts)
        self.assertIn('kosher', conflicts)
        self.assertIn('keto', conflicts)
        self.assertIn('paleo', conflicts)
        self.assertIn('low_sugar', conflicts)
        
    def test_is_safe_for_user_with_allergens(self):
        """Test safety check for a user with allergens"""
        # User with dairy allergy
        user_allergens = ['dairy']
        
        # Milk product should not be safe
        safety = AllergenDetector.is_safe_for_user(self.milk_product, user_allergens)
        self.assertFalse(safety['is_safe'])
        self.assertEqual(len(safety['allergen_conflicts']), 1)
        self.assertEqual(safety['allergen_conflicts'][0]['category'], 'dairy')
        
        # Cereal product should be safe
        safety = AllergenDetector.is_safe_for_user(self.cereal_product, user_allergens)
        self.assertTrue(safety['is_safe'])
        self.assertEqual(len(safety['allergen_conflicts']), 0)
        
    def test_is_safe_for_user_with_preferences(self):
        """Test safety check for a user with dietary preferences"""
        # User with vegan preference
        user_preferences = ['vegan']
        
        # Vegetable soup should be safe for vegans
        safety = AllergenDetector.is_safe_for_user(self.vegetarian_product, user_preferences=user_preferences)
        self.assertTrue(safety['is_safe'])
        self.assertEqual(len(safety['preference_conflicts']), 0)
        
        # Chicken soup should not be safe for vegans
        safety = AllergenDetector.is_safe_for_user(self.non_vegetarian_product, user_preferences=user_preferences)
        self.assertFalse(safety['is_safe'])
        self.assertEqual(len(safety['preference_conflicts']), 1)
        self.assertEqual(safety['preference_conflicts'][0]['preference'], 'vegan')
        
    def test_is_safe_for_user_unknown(self):
        """Test safety check for products with missing information"""
        user_allergens = ['dairy']
        safety = AllergenDetector.is_safe_for_user(self.unknown_product, user_allergens)
        self.assertEqual(safety['is_safe'], 'unknown')
        self.assertIn('No ingredients information available', safety['warnings'])
        
    def test_filter_products(self):
        """Test filtering a list of products based on user preferences"""
        # List of test products
        products = [
            self.milk_product,
            self.cereal_product,
            self.candy_product,
            self.unknown_product,
            self.vegetarian_product,
            self.non_vegetarian_product
        ]
        
        # User with dairy allergy and vegan preference
        user_allergens = ['dairy']
        user_preferences = ['vegan']
        
        safe, unsafe, unknown = AllergenDetector.filter_products(
            products, user_allergens, user_preferences
        )
        
        # Only the vegetable soup and cereal should be safe
        self.assertEqual(len(safe), 2)
        self.assertTrue(any(p['name'] == 'Vegetable Soup' for p in safe))
        self.assertTrue(any(p['name'] == 'Wheat Cereal' for p in safe))
        
        # Milk, candy, and chicken soup should be unsafe
        self.assertEqual(len(unsafe), 3)
        self.assertTrue(any(p['name'] == 'Milk' for p in unsafe))
        self.assertTrue(any(p['name'] == 'Chocolate Bar' for p in unsafe))
        self.assertTrue(any(p['name'] == 'Chicken Soup' for p in unsafe))
        
        # Mystery product should have unknown safety
        self.assertEqual(len(unknown), 1)
        self.assertTrue(any(p['name'] == 'Mystery Product' for p in unknown))