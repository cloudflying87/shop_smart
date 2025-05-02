import json
import time
import requests
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from shopping.models import GroceryItem, ProductCategory, GroceryStore, ItemStoreInfo

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Populates the database with products from Open Food Facts API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--categories',
            type=str,
            nargs='+',
            help='Specific categories to import (e.g. "dairy" "fruits" "vegetables")'
        )
        
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of products to import per category (default: 100)'
        )
        
        parser.add_argument(
            '--country',
            type=str,
            default='us',
            help='Country to filter products by (default: us)'
        )
        
        parser.add_argument(
            '--wait',
            type=float,
            default=1.0,
            help='Wait time between API requests in seconds (default: 1.0)'
        )
        
        parser.add_argument(
            '--store',
            type=str,
            help='Associate imported products with this store (store slug)'
        )
        
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing products instead of skipping them'
        )

    def handle(self, *args, **options):
        categories = options['categories']
        count_per_category = options['count']
        country = options['country']
        wait_time = options['wait']
        store_slug = options['store']
        update_existing = options['update']
        
        # Initialize store if specified
        store = None
        if store_slug:
            try:
                store = GroceryStore.objects.get(slug=store_slug)
                self.stdout.write(self.style.SUCCESS(f"Found store: {store.name}"))
            except GroceryStore.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Store with slug '{store_slug}' not found"))
                return
        
        # If no categories specified, use default common categories
        if not categories:
            categories = [
                'dairy', 'fruits', 'vegetables', 'meat', 'seafood',
                'bakery', 'cereals', 'snacks', 'beverages', 'frozen-foods',
                'canned-foods', 'condiments', 'spices', 'baking', 'pasta'
            ]
            self.stdout.write(f"Using default categories: {', '.join(categories)}")
        
        # Process each category
        for category in categories:
            self.stdout.write(f"Processing category: {category}")
            self._import_category_products(
                category, 
                count_per_category, 
                country, 
                wait_time, 
                store, 
                update_existing
            )
            
        self.stdout.write(self.style.SUCCESS('Product import completed successfully'))

    def _import_category_products(self, category, count, country, wait_time, store, update_existing):
        """Import products for a specific category"""
        
        base_url = "https://world.openfoodfacts.org/cgi/search.pl"
        
        # We'll need to paginate to get the requested count
        page_size = min(count, 100)  # Max page size is 100
        pages = (count + page_size - 1) // page_size
        
        # Get or create category
        category_obj, created = ProductCategory.objects.get_or_create(
            name=category.replace('-', ' ').title(),
            defaults={
                'sort_order': 0,
                'icon': self._get_category_icon(category)
            }
        )
        
        if created:
            self.stdout.write(f"Created new category: {category_obj.name}")
        
        # Track statistics
        total_imported = 0
        total_updated = 0
        total_skipped = 0
        
        # Process each page
        for page in range(1, pages + 1):
            params = {
                'action': 'process',
                'tagtype_0': 'categories',
                'tag_contains_0': 'contains',
                'tag_0': category,
                'tagtype_1': 'countries',
                'tag_contains_1': 'contains',
                'tag_1': country,
                'page_size': page_size,
                'page': page,
                'json': 1
            }
            
            try:
                # Make API request
                self.stdout.write(f"Fetching page {page} of {pages} for {category}")
                response = requests.get(base_url, params=params)
                
                if response.status_code != 200:
                    self.stdout.write(self.style.ERROR(
                        f"Error fetching products: HTTP {response.status_code}"
                    ))
                    continue
                
                data = response.json()
                products = data.get('products', [])
                
                if not products:
                    self.stdout.write(f"No products found for category {category} on page {page}")
                    break
                
                # Process products
                for product in products:
                    result = self._process_product(product, category_obj, store, update_existing)
                    
                    if result == 'imported':
                        total_imported += 1
                    elif result == 'updated':
                        total_updated += 1
                    else:  # skipped
                        total_skipped += 1
                
                # Wait between requests to avoid rate limiting
                time.sleep(wait_time)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing category {category}: {str(e)}"))
                logger.exception(f"Error in import_category_products for {category}")
        
        # Print summary
        self.stdout.write(self.style.SUCCESS(
            f"Category {category}: {total_imported} imported, {total_updated} updated, {total_skipped} skipped"
        ))

    def _process_product(self, product, category, store, update_existing):
        """Process a single product"""
        
        # Extract product information
        barcode = product.get('code', '')
        name = product.get('product_name', '')
        
        # Skip products without barcode or name
        if not barcode or not name:
            return 'skipped'
        
        # Check if product already exists
        existing_product = GroceryItem.objects.filter(barcode=barcode).first()
        
        # If product exists and we're not updating, skip it
        if existing_product and not update_existing:
            return 'skipped'
        
        try:
            with transaction.atomic():
                # Prepare product data
                product_data = {
                    'name': name,
                    'description': product.get('ingredients_text', ''),
                    'brand': product.get('brands', ''),
                    'image_url': product.get('image_url', ''),
                    'off_id': product.get('id', ''),
                    'is_verified': True,
                    'category': category
                }
                
                if existing_product and update_existing:
                    # Update existing product
                    for key, value in product_data.items():
                        setattr(existing_product, key, value)
                    
                    existing_product.save()
                    product_obj = existing_product
                    result = 'updated'
                else:
                    # Create new product
                    product_obj = GroceryItem.objects.create(
                        barcode=barcode,
                        **product_data
                    )
                    result = 'imported'
                
                # If store is specified, create store info
                if store and product_obj:
                    # Get or create store info
                    store_info, _ = ItemStoreInfo.objects.get_or_create(
                        item=product_obj,
                        store=store,
                        defaults={
                            'typical_price': self._extract_price(product),
                        }
                    )
                
                return result
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing product {barcode}: {str(e)}"))
            logger.exception(f"Error in _process_product for {barcode}")
            return 'skipped'

    def _extract_price(self, product):
        """Extract price from product data if available"""
        try:
            # This is a simplification as OFF doesn't have consistent price data
            # In a real app, you'd need a more sophisticated approach
            if 'nutriments' in product and 'price-per-kg' in product['nutriments']:
                return float(product['nutriments']['price-per-kg']) / 100
            return None
        except (ValueError, TypeError):
            return None

    def _get_category_icon(self, category):
        """Get icon name for a category"""
        icons = {
            'dairy': 'milk',
            'fruits': 'apple',
            'vegetables': 'carrot',
            'meat': 'meat',
            'seafood': 'fish',
            'bakery': 'bread',
            'cereals': 'cereal',
            'snacks': 'cookie',
            'beverages': 'beer',
            'frozen-foods': 'snow',
            'canned-foods': 'can',
            'condiments': 'sauce',
            'spices': 'pepper',
            'baking': 'cake',
            'pasta': 'pasta',
            'cleaning': 'spray',
            'personal-care': 'shower',
            'baby': 'baby',
            'pet': 'pet',
            'alcohol': 'wine'
        }
        
        return icons.get(category.lower(), 'grocery')