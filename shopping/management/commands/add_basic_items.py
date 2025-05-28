import csv
from django.core.management.base import BaseCommand
from shopping.models import GroceryItem, ProductCategory


class Command(BaseCommand):
    help = 'Add basic grocery items without brands'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-categories',
            action='store_true',
            help='Update categories for existing items without affecting store associations'
        )

    def handle(self, *args, **options):
        # Define basic food categories and items
        basic_items = {
            'Fruits': [
                'Apples', 'Oranges', 'Bananas', 'Grapes', 'Strawberries', 'Blueberries',
                'Raspberries', 'Blackberries', 'Pineapple', 'Watermelon', 'Cantaloupe',
                'Honeydew', 'Kiwi', 'Mango', 'Peaches', 'Plums', 'Pears', 'Cherries',
                'Avocados', 'Lemons', 'Limes'
            ],
            'Vegetables': [
                'Tomatoes', 'Potatoes', 'Sweet Potatoes', 'Carrots', 'Onions',
                'Broccoli', 'Cauliflower', 'Spinach', 'Kale', 'Lettuce', 'Cabbage',
                'Bell Peppers', 'Mushrooms', 'Garlic', 'Ginger', 'Cucumber', 'Zucchini',
                'Celery', 'Green Beans', 'Corn', 'Radishes', 'Green Onions',
                'Asparagus', 'Eggplant', 'Brussels Sprouts', 'Squash', 'Artichokes', 'Beets'
            ],
            'Dairy': [
                'Milk', 'Butter', 'Eggs', 'Yogurt', 'Cheese', 'Cottage Cheese', 'Cream Cheese',
                'Sour Cream', 'Whipping Cream', 'Half and Half', 'Cheddar Cheese',
                'Mozzarella Cheese', 'Swiss Cheese', 'Parmesan Cheese', 'Ricotta Cheese',
                'Greek Yogurt', 'Buttermilk', 'Almond Milk', 'Soy Milk', 'Oat Milk',
                'Heavy Cream', 'Ice Cream', 'Margarine', 'Whipped Cream', 'Feta Cheese','Organic Almond Milk'
            ],
            'Meat': [
                'Chicken Breast', 'Ground Beef', 'Steak', 'Pork Chops', 'Bacon', 'Ham',
                'Turkey', 'Ground Turkey', 'Sausage', 'Hot Dogs', 'Salami', 'Lunch Meat',
                'Ground Pork', 'Lamb Chops', 'Beef Roast', 'Pork Roast', 'Chicken Thighs',
                'Chicken Wings', 'Ribs', 'Beef Jerky', 'Pepperoni', 'Corned Beef', 'Pastrami'
            ],
            'Seafood': [
                'Salmon', 'Tuna', 'Tilapia', 'Cod', 'Halibut', 'Crab', 'Lobster', 'Shrimp',
                'Scallops', 'Clams', 'Mussels', 'Oysters', 'Trout', 'Catfish', 'Sardines',
                'Flounder', 'Sea Bass', 'Swordfish', 'Mahi Mahi', 'Canned Tuna', 'Canned Salmon'
            ],
            'Bakery': [
                'Bread', 'Bagels', 'Muffins', 'Croissants', 'English Muffins', 'Baguette',
                'Rolls', 'Hamburger Buns', 'Hot Dog Buns', 'Tortillas', 'Pita Bread',
                'Naan', 'Cake', 'Pie', 'Cookies', 'Brownies', 'Donuts', 'Biscuits',
                'Cinnamon Rolls', 'Coffee Cake', 'Crackers', 'Bread Crumbs', 'Croutons',
                'Dinner Rolls', 'Cornbread', 'Sourdough Bread', 'Rye Bread', 'Whole Wheat Bread'
            ],
            'Spices': [
                'Salt', 'Black Pepper', 'Garlic Powder', 'Onion Powder', 'Paprika',
                'Cayenne Pepper', 'Chili Powder', 'Cumin', 'Oregano', 'Basil',
                'Thyme', 'Rosemary', 'Sage', 'Bay Leaves', 'Cinnamon', 'Nutmeg',
                'Ginger Powder', 'Turmeric', 'Coriander', 'Cardamom', 'Cloves',
                'Allspice', 'Mustard Powder', 'Curry Powder', 'Italian Seasoning',
                'Taco Seasoning', 'Cajun Seasoning', 'Everything Bagel Seasoning',
                'Sesame Seeds', 'Poppy Seeds', 'Fennel Seeds', 'Crushed Red Pepper',
                'White Pepper', 'Smoked Paprika', 'Dill', 'Parsley', 'Cilantro',
                'Mint', 'Vanilla Extract', 'Almond Extract', 'Lemon Extract',
                'Sweet Paprika', 'Smoked Peppercorns', 'Guajillo Chili Peppers',
                'Gochugaru', 'Black Garlic', 'Stir-Fry Seasoning', 'Buffalo Seasoning',
                'Breakfast Sausage Seasoning', 'BBQ Seasoning', 'Ranch Seasoning',
                'Chipotle Powder', 'Ancho Chili Powder', 'Garlic Salt', 'Onion Salt',
                'Celery Salt', 'Seasoned Salt', 'Lemon Pepper', 'Montreal Steak Seasoning',
                'Old Bay Seasoning', 'Poultry Seasoning', 'Pumpkin Pie Spice',
                'Apple Pie Spice', 'Chinese Five Spice', 'Herbes de Provence',
                'Za\'atar', 'Sumac', 'Harissa', 'Ras el Hanout', 'Garam Masala',
                'Tandoori Masala', 'Curry Leaves', 'Fenugreek', 'Nigella Seeds',
                'Star Anise', 'Juniper Berries', 'Mace', 'Long Pepper', 'Pink Peppercorns',
                'Szechuan Peppercorns', 'Chili Flakes', 'Chipotle Flakes', 'Smoked Salt',
                'Himalayan Pink Salt', 'Sea Salt', 'Kosher Salt', 'Flaky Sea Salt'
            ],
            'Pantry': [
                'Rice', 'Pasta', 'Flour', 'Sugar', 'Cooking Oil',
                'Olive Oil', 'Vinegar', 'Soy Sauce', 'Ketchup', 'Mustard', 'Mayonnaise',
                'Peanut Butter', 'Jelly', 'Honey', 'Maple Syrup', 'Coffee', 'Tea',
                'Cereal', 'Oatmeal', 'Pancake Mix', 'Canned Soup', 'Canned Beans',
                'Canned Tuna', 'Canned Tomatoes', 'Tomato Sauce', 'Pasta Sauce',
                'Chicken Broth', 'Beef Broth', 'Vegetable Broth', 'Hot Sauce',
                'BBQ Sauce', 'Salsa', 'Salad Dressing', 'Pickles', 'Olives', 'Jam',
                'Canned Corn', 'Canned Fruit', 'Granola', 'Baking Powder', 'Baking Soda',
                'Chocolate Chips', 'Brown Sugar', 'Powdered Sugar'
            ],
            'Snacks': [
                'Potato Chips', 'Tortilla Chips', 'Pretzels', 'Popcorn', 'Crackers',
                'Nuts', 'Trail Mix', 'Granola Bars', 'Chocolate', 'Candy', 'Dried Fruit',
                'Jerky', 'Rice Cakes', 'Fruit Snacks', 'Cookies', 'Pudding', 'Jello',
                'Protein Bars', 'Peanuts', 'Almonds', 'Cashews', 'Sunflower Seeds',
                'Popcorn', 'Hummus', 'Salsa', 'Guacamole', 'Cheese Sticks','Veggie Sticks'
            ],
            'Beverages': [
                'Water', 'Soda', 'Juice', 'Coffee', 'Tea', 'Beer', 'Wine', 'Milk',
                'Almond Milk', 'Soy Milk', 'Coconut Milk', 'Sparkling Water',
                'Energy Drinks', 'Sports Drinks', 'Hot Chocolate', 'Lemonade', 'Iced Tea',
                'Apple Juice', 'Orange Juice', 'Cranberry Juice', 'Grapefruit Juice',
                'Kombucha', 'Cold Brew', 'Hard Seltzer', 'Liquor', 'Protein Shakes'
            ],
            'Frozen': [
                'Ice Cream', 'Frozen Pizza', 'Frozen Vegetables', 'Frozen Fruit',
                'Frozen Dinners', 'Frozen Breakfast', 'Frozen Appetizers', 'Popsicles',
                'Frozen Waffles', 'Frozen Pancakes', 'Frozen Fries', 'Frozen Fish',
                'Frozen Chicken', 'Frozen Desserts', 'Frozen Burritos', 'Frozen Lasagna',
                'Frozen Pie', 'Frozen Smoothie Mix', 'Frozen Meatballs', 'Frozen Stir Fry'
            ],
            'Household': [
                'Toilet Paper', 'Paper Towels', 'Tissues', 'Dish Soap', 'Laundry Detergent',
                'Fabric Softener', 'Bleach', 'All-Purpose Cleaner', 'Glass Cleaner',
                'Bathroom Cleaner', 'Floor Cleaner', 'Disinfecting Wipes', 'Sponges',
                'Trash Bags', 'Sandwich Bags', 'Plastic Wrap', 'Aluminum Foil', 'Parchment Paper',
                'Food Storage Containers', 'Light Bulbs', 'Batteries', 'Air Freshener',
                'Candles', 'Matches', 'Dish Scrubber', 'Dishwasher Detergent', 'Dryer Sheets',
                'Mop Refills', 'Broom', 'Dustpan', 'Vacuum Bags', 'Furniture Polish'
            ],
            'Personal Care': [
                'Shampoo', 'Conditioner', 'Body Wash', 'Bar Soap', 'Deodorant', 'Lotion',
                'Toothpaste', 'Mouthwash', 'Dental Floss', 'Toothbrushes', 'Razor Blades',
                'Shaving Cream', 'Feminine Products', 'Cotton Swabs', 'Cotton Balls',
                'Bandages', 'First Aid Supplies', 'Vitamins', 'Pain Relievers', 'Antacids',
                'Allergy Medicine', 'Cold Medicine', 'Hand Sanitizer', 'Sunscreen',
                'Lip Balm', 'Makeup Remover', 'Hair Gel', 'Hair Spray', 'Body Lotion',
                'Face Wash', 'Face Moisturizer', 'Hand Soap', 'Contact Solution'
            ],
            'Baby & Pet': [
                'Diapers', 'Baby Wipes', 'Baby Formula', 'Baby Food', 'Baby Shampoo',
                'Baby Lotion', 'Baby Powder', 'Bottles', 'Pacifiers', 'Teething Toys',
                'Dog Food', 'Cat Food', 'Pet Treats', 'Cat Litter', 'Pet Toys',
                'Pet Shampoo', 'Flea Treatment', 'Pet Waste Bags', 'Pet Bedding'
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
        
        # Handle category updates if requested
        if options.get('update_categories'):
            self.update_existing_categories(basic_items)
    
    def update_existing_categories(self, basic_items):
        """Update categories for existing items without affecting store associations"""
        self.stdout.write("Updating categories for existing items...")
        update_count = 0
        
        for category_name, items in basic_items.items():
            # Get or create the category
            category, created = ProductCategory.objects.get_or_create(
                name=category_name,
                defaults={'sort_order': 0}
            )
            
            # Update items that exist but may have wrong category
            for item_name in items:
                try:
                    item = GroceryItem.objects.get(name=item_name)
                    if item.category.name != category_name:
                        old_category = item.category.name
                        item.category = category
                        item.save()
                        update_count += 1
                        self.stdout.write(
                            f"Updated '{item_name}' from category '{old_category}' to '{category_name}'"
                        )
                except GroceryItem.DoesNotExist:
                    # Item doesn't exist, skip it
                    pass
                except GroceryItem.MultipleObjectsReturned:
                    # Multiple items with same name, update all
                    items_to_update = GroceryItem.objects.filter(name=item_name)
                    for item in items_to_update:
                        if item.category.name != category_name:
                            old_category = item.category.name
                            item.category = category
                            item.save()
                            update_count += 1
                            self.stdout.write(
                                f"Updated '{item_name}' (ID: {item.id}) from category '{old_category}' to '{category_name}'"
                            )
        
        self.stdout.write(
            self.style.SUCCESS(f"Successfully updated {update_count} items to new categories")
        )