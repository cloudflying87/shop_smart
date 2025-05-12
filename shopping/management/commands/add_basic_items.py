import csv
from django.core.management.base import BaseCommand
from shopping.models import GroceryItem, ProductCategory


class Command(BaseCommand):
    help = 'Add basic grocery items without brands'

    def handle(self, *args, **options):
        # Define basic food categories and items
        basic_items = {
            'Produce': [
                'Apples', 'Oranges', 'Bananas', 'Grapes', 'Strawberries', 'Blueberries',
                'Raspberries', 'Blackberries', 'Pineapple', 'Watermelon', 'Cantaloupe',
                'Honeydew', 'Kiwi', 'Mango', 'Peaches', 'Plums', 'Pears', 'Cherries',
                'Avocados', 'Tomatoes', 'Potatoes', 'Sweet Potatoes', 'Carrots', 'Onions',
                'Broccoli', 'Cauliflower', 'Spinach', 'Kale', 'Lettuce', 'Cabbage',
                'Bell Peppers', 'Mushrooms', 'Garlic', 'Ginger', 'Cucumber', 'Zucchini', 
                'Celery', 'Green Beans', 'Corn', 'Radishes'
            ],
            'Dairy': [
                'Milk', 'Butter', 'Eggs', 'Yogurt', 'Cheese', 'Cottage Cheese', 'Cream Cheese',
                'Sour Cream', 'Whipping Cream', 'Half and Half', 'Cheddar Cheese',
                'Mozzarella Cheese', 'Swiss Cheese', 'Parmesan Cheese', 'Ricotta Cheese',
                'Greek Yogurt', 'Buttermilk'
            ],
            'Meat': [
                'Chicken Breast', 'Ground Beef', 'Steak', 'Pork Chops', 'Bacon', 'Ham',
                'Turkey', 'Ground Turkey', 'Sausage', 'Hot Dogs', 'Salami', 'Lunch Meat',
                'Ground Pork', 'Lamb Chops', 'Beef Roast', 'Pork Roast'
            ],
            'Seafood': [
                'Salmon', 'Tuna', 'Tilapia', 'Cod', 'Halibut', 'Crab', 'Lobster', 'Shrimp',
                'Scallops', 'Clams', 'Mussels', 'Oysters', 'Trout', 'Catfish', 'Sardines'
            ],
            'Bakery': [
                'Bread', 'Bagels', 'Muffins', 'Croissants', 'English Muffins', 'Baguette',
                'Rolls', 'Hamburger Buns', 'Hot Dog Buns', 'Tortillas', 'Pita Bread',
                'Naan', 'Cake', 'Pie', 'Cookies', 'Brownies', 'Donuts'
            ],
            'Pantry': [
                'Rice', 'Pasta', 'Flour', 'Sugar', 'Salt', 'Pepper', 'Cooking Oil',
                'Olive Oil', 'Vinegar', 'Soy Sauce', 'Ketchup', 'Mustard', 'Mayonnaise',
                'Peanut Butter', 'Jelly', 'Honey', 'Maple Syrup', 'Coffee', 'Tea',
                'Cereal', 'Oatmeal', 'Pancake Mix', 'Canned Soup', 'Canned Beans',
                'Canned Tuna', 'Canned Tomatoes', 'Tomato Sauce', 'Pasta Sauce',
                'Chicken Broth', 'Beef Broth', 'Vegetable Broth', 'Spices'
            ],
            'Snacks': [
                'Potato Chips', 'Tortilla Chips', 'Pretzels', 'Popcorn', 'Crackers',
                'Nuts', 'Trail Mix', 'Granola Bars', 'Chocolate', 'Candy', 'Dried Fruit',
                'Jerky', 'Rice Cakes', 'Fruit Snacks', 'Cookies', 'Pudding', 'Jello'
            ],
            'Beverages': [
                'Water', 'Soda', 'Juice', 'Coffee', 'Tea', 'Beer', 'Wine', 'Milk',
                'Almond Milk', 'Soy Milk', 'Coconut Milk', 'Sparkling Water',
                'Energy Drinks', 'Sports Drinks', 'Hot Chocolate', 'Lemonade', 'Iced Tea'
            ],
            'Frozen': [
                'Ice Cream', 'Frozen Pizza', 'Frozen Vegetables', 'Frozen Fruit',
                'Frozen Dinners', 'Frozen Breakfast', 'Frozen Appetizers', 'Popsicles',
                'Frozen Waffles', 'Frozen Pancakes', 'Frozen Fries', 'Frozen Fish',
                'Frozen Chicken', 'Frozen Desserts'
            ]
        }

        # Create items by category
        item_count = 0
        for category_name, items in basic_items.items():
            # Get or create category
            category, created = ProductCategory.objects.get_or_create(
                name=category_name,
                defaults={'sort_order': 0}
            )
            
            if created:
                self.stdout.write(f"Created category: {category_name}")
            
            # Add items in this category
            for item_name in items:
                # Skip if item already exists
                if GroceryItem.objects.filter(name=item_name).exists():
                    self.stdout.write(f"Skipping existing item: {item_name}")
                    continue
                
                # Create new item
                GroceryItem.objects.create(
                    name=item_name,
                    description=f"Basic {item_name}",
                    category=category,
                    global_popularity=10,
                    is_verified=True
                )
                item_count += 1
                self.stdout.write(f"Added item: {item_name} ({category_name})")
        
        self.stdout.write(self.style.SUCCESS(f"Successfully added {item_count} basic grocery items"))