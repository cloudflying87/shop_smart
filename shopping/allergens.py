"""
Allergen and Dietary Preferences Management for ShopSmart

This module provides functionality to handle food allergens and dietary preferences,
including allergen detection, preference filtering, and product recommendations.
"""

# Common allergens based on international food labeling standards
COMMON_ALLERGENS = {
    'gluten': ['wheat', 'barley', 'rye', 'oats', 'spelt', 'kamut', 'triticum', 'gluten'],
    'dairy': ['milk', 'cream', 'cheese', 'butter', 'yogurt', 'whey', 'lactose', 'casein', 'dairy'],
    'eggs': ['egg', 'eggs', 'albumin', 'globulin', 'ovoglobulin', 'livetin', 'ovomucoid', 'ovovitellin'],
    'nuts': ['almond', 'hazelnut', 'walnut', 'cashew', 'pecan', 'brazil nut', 'pistachio', 'macadamia', 'nuts'],
    'peanuts': ['peanut', 'arachis', 'groundnut'],
    'soy': ['soy', 'soya', 'soybean', 'glycine max'],
    'fish': ['fish', 'cod', 'salmon', 'tuna', 'bass', 'trout', 'seafood'],
    'shellfish': ['shrimp', 'crab', 'lobster', 'prawn', 'crayfish', 'shellfish', 'crustacean'],
    'sesame': ['sesame', 'tahini', 'sesame oil', 'sesame seed'],
    'mustard': ['mustard', 'mustard seed', 'mustard powder'],
    'celery': ['celery', 'celeriac'],
    'lupin': ['lupin', 'lupine', 'lupin flour', 'lupin seed'],
    'molluscs': ['oyster', 'mussel', 'clam', 'scallop', 'octopus', 'squid', 'snail', 'mollusc', 'mollusk'],
    'sulfites': ['sulfite', 'sulphite', 'sulfur dioxide', 'so2', 'e220', 'e221', 'e222', 'e223', 'e224', 'e225', 'e226', 'e227', 'e228']
}

# Dietary preferences
DIETARY_PREFERENCES = {
    'vegan': {
        'avoid': ['meat', 'poultry', 'fish', 'seafood', 'dairy', 'egg', 'honey', 'gelatin', 'casein', 'whey'],
        'description': 'No animal products or by-products'
    },
    'vegetarian': {
        'avoid': ['meat', 'poultry', 'fish', 'seafood', 'gelatin', 'rennet'],
        'description': 'No meat, poultry, fish, or seafood'
    },
    'pescatarian': {
        'avoid': ['meat', 'poultry'],
        'description': 'No meat or poultry, but allows fish and seafood'
    },
    'keto': {
        'avoid': ['sugar', 'flour', 'corn', 'potato', 'rice', 'grain', 'starch', 'honey', 'agave'],
        'description': 'Low carb, high fat diet'
    },
    'paleo': {
        'avoid': ['dairy', 'grain', 'legume', 'processed', 'refined sugar', 'potato', 'salt'],
        'description': 'Focuses on whole foods that were available to our paleolithic ancestors'
    },
    'halal': {
        'avoid': ['pork', 'alcohol', 'blood', 'gelatin'],
        'description': 'Follows Islamic dietary laws'
    },
    'kosher': {
        'avoid': ['pork', 'shellfish', 'rabbit'],
        'description': 'Follows Jewish dietary laws'
    },
    'low_sodium': {
        'avoid': ['salt', 'sodium', 'msg', 'baking soda', 'baking powder', 'disodium', 'monosodium'],
        'description': 'Restricted sodium intake'
    },
    'low_sugar': {
        'avoid': ['sugar', 'sucrose', 'glucose', 'fructose', 'corn syrup', 'honey', 'agave', 'molasses'],
        'description': 'Restricted sugar intake'
    }
}


class AllergenDetector:
    """
    Detect allergens and dietary preference conflicts in product ingredients 
    and provide filtering capabilities.
    """
    
    @classmethod
    def detect_allergens(cls, product_data):
        """
        Detect allergens in a product based on ingredients and allergen tags
        
        Args:
            product_data (dict): Product data that includes 'ingredients' or 'allergens'
            
        Returns:
            dict: Detected allergens by category
        """
        detected = {}
        
        # Check direct allergen tags if available
        if product_data.get('allergens') and isinstance(product_data['allergens'], list):
            for allergen in product_data['allergens']:
                for category, keywords in COMMON_ALLERGENS.items():
                    if any(keyword.lower() in allergen.lower() for keyword in keywords):
                        if category not in detected:
                            detected[category] = []
                        detected[category].append(allergen)
        
        # Check ingredients text
        ingredients_text = product_data.get('ingredients', '') or ''
        if isinstance(ingredients_text, str) and ingredients_text:
            ingredients_lower = ingredients_text.lower()
            
            for category, keywords in COMMON_ALLERGENS.items():
                for keyword in keywords:
                    if keyword.lower() in ingredients_lower:
                        if category not in detected:
                            detected[category] = []
                        if keyword not in detected[category]:
                            detected[category].append(keyword)
        
        return detected
    
    @classmethod
    def check_dietary_preferences(cls, product_data):
        """
        Check if a product conflicts with various dietary preferences
        
        Args:
            product_data (dict): Product data that includes 'ingredients'
            
        Returns:
            dict: Conflicts by dietary preference
        """
        conflicts = {}
        
        # Extract ingredients text
        ingredients_text = product_data.get('ingredients', '') or ''
        if not isinstance(ingredients_text, str) or not ingredients_text:
            return conflicts
        
        ingredients_lower = ingredients_text.lower()
        
        # Check each dietary preference
        for preference, data in DIETARY_PREFERENCES.items():
            avoid_ingredients = data['avoid']
            
            # Track specific conflicts
            found_conflicts = []
            
            for ingredient in avoid_ingredients:
                if ingredient.lower() in ingredients_lower:
                    found_conflicts.append(ingredient)
            
            if found_conflicts:
                conflicts[preference] = found_conflicts
        
        return conflicts
    
    @classmethod
    def is_safe_for_user(cls, product_data, user_allergens=None, user_preferences=None):
        """
        Check if a product is safe for a user based on their allergens and preferences
        
        Args:
            product_data (dict): Product data
            user_allergens (list): List of user's allergen categories
            user_preferences (list): List of user's dietary preferences
            
        Returns:
            dict: Safety assessment with details
        """
        result = {
            'is_safe': True,
            'allergen_conflicts': [],
            'preference_conflicts': [],
            'warnings': []
        }
        
        # Check allergens if user has specified any
        if user_allergens:
            detected_allergens = cls.detect_allergens(product_data)
            
            for allergen in user_allergens:
                if allergen in detected_allergens:
                    result['is_safe'] = False
                    result['allergen_conflicts'].append({
                        'category': allergen,
                        'detected': detected_allergens[allergen]
                    })
        
        # Check dietary preferences if user has specified any
        if user_preferences:
            preference_conflicts = cls.check_dietary_preferences(product_data)
            
            for preference in user_preferences:
                if preference in preference_conflicts:
                    result['is_safe'] = False
                    result['preference_conflicts'].append({
                        'preference': preference,
                        'conflicts': preference_conflicts[preference],
                        'description': DIETARY_PREFERENCES[preference]['description']
                    })
        
        # Add warnings if ingredients list is missing or incomplete
        if not product_data.get('ingredients'):
            result['warnings'].append('No ingredients information available')
            
        if result['is_safe'] and (result['warnings'] or not product_data.get('ingredients')):
            result['is_safe'] = 'unknown'
            
        return result
    
    @classmethod
    def filter_products(cls, products, user_allergens=None, user_preferences=None):
        """
        Filter a list of products based on user allergens and preferences
        
        Args:
            products (list): List of product data dictionaries
            user_allergens (list): List of user's allergen categories
            user_preferences (list): List of user's dietary preferences
            
        Returns:
            tuple: (safe_products, unsafe_products, unknown_safety_products)
        """
        safe_products = []
        unsafe_products = []
        unknown_safety_products = []
        
        for product in products:
            safety = cls.is_safe_for_user(product, user_allergens, user_preferences)
            
            if safety['is_safe'] is True:
                safe_products.append(product)
            elif safety['is_safe'] == 'unknown':
                unknown_safety_products.append(product)
            else:
                unsafe_products.append(product)
        
        return safe_products, unsafe_products, unknown_safety_products