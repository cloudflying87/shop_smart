"""
Open Food Facts API Integration for ShopSmart

This module provides comprehensive integration with the Open Food Facts API,
handling data retrieval, caching, and error handling.
"""

import requests
from urllib.parse import quote
import json
import logging
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# Cache settings - can be overridden in Django settings
CACHE_TIMEOUT = getattr(settings, 'OFF_CACHE_TIMEOUT', 60 * 60 * 24)  # 24 hours default
SEARCH_CACHE_TIMEOUT = getattr(settings, 'OFF_SEARCH_CACHE_TIMEOUT', 60 * 60)  # 1 hour default

class OpenFoodFactsAPI:
    """
    Client for interacting with the Open Food Facts API.
    
    Features:
    - Robust error handling
    - Response caching
    - Rate limiting protection
    - Comprehensive product data retrieval
    - Search capabilities
    """
    
    BASE_URL = 'https://world.openfoodfacts.org/api/v0'
    USER_AGENT = 'ShopSmart - Django Shopping App'
    
    @classmethod
    def get_product(cls, barcode):
        """
        Fetch a product by barcode from Open Food Facts API.
        
        Args:
            barcode (str): Product barcode (UPC, EAN, etc.)
            
        Returns:
            dict: Normalized product data or None if not found
        """
        # Check cache first
        cache_key = f'off_product_{barcode}'
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for barcode {barcode}")
            return cached_data
        
        try:
            # Make API request
            url = f"{cls.BASE_URL}/product/{barcode}.json"
            headers = {'User-Agent': cls.USER_AGENT}
            
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if product was found
            if data.get('status') != 1 or 'product' not in data:
                logger.info(f"Product with barcode {barcode} not found")
                return None
            
            # Normalize and extract relevant product data
            product_data = cls._normalize_product_data(data['product'])
            
            # Cache the results
            cache.set(cache_key, product_data, CACHE_TIMEOUT)
            
            return product_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching product {barcode}: {str(e)}")
            return None
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing product data for {barcode}: {str(e)}")
            return None
    
    @classmethod
    def search_products(cls, query, page=1, page_size=20, categories=None, brands=None):
        """
        Search for products in Open Food Facts.
        
        Args:
            query (str): Search query
            page (int): Page number for pagination
            page_size (int): Number of results per page
            categories (list): Optional list of categories to filter by
            brands (list): Optional list of brands to filter by
            
        Returns:
            dict: Search results with products and pagination info
        """
        # Create cache key based on all parameters
        cache_params = f"{query}_{page}_{page_size}"
        if categories:
            cache_params += f"_cats={'_'.join(categories)}"
        if brands:
            cache_params += f"_brands={'_'.join(brands)}"
        
        cache_key = f'off_search_{hash(cache_params)}'
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for search: {query}")
            return cached_data
        
        try:
            # Build search URL
            url = f"{cls.BASE_URL}/search"
            
            # Build parameters
            params = {
                'search_terms': query,
                'page': page,
                'page_size': page_size,
                'json': 1,
            }
            
            # Add filter parameters if provided
            if categories:
                params['tagtype_0'] = 'categories'
                params['tag_contains_0'] = 'contains'
                params['tag_0'] = ','.join(categories)
                
            if brands:
                tag_index = 1 if categories else 0
                params[f'tagtype_{tag_index}'] = 'brands'
                params[f'tag_contains_{tag_index}'] = 'contains'
                params[f'tag_{tag_index}'] = ','.join(brands)
            
            # Make API request
            headers = {'User-Agent': cls.USER_AGENT}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Normalize result data
            result = {
                'products': [cls._normalize_product_data(p) for p in data.get('products', [])],
                'total': data.get('count', 0),
                'page': data.get('page', page),
                'page_size': data.get('page_size', page_size),
                'total_pages': data.get('page_count', 0)
            }
            
            # Cache the results (shorter time than individual products)
            cache.set(cache_key, result, SEARCH_CACHE_TIMEOUT)
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching products: {str(e)}")
            return {'products': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing search results: {str(e)}")
            return {'products': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
    
    @classmethod
    def get_categories(cls):
        """
        Get popular product categories from Open Food Facts.
        
        Returns:
            list: List of category data dictionaries
        """
        cache_key = 'off_categories'
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            url = f"{cls.BASE_URL}/categories.json"
            headers = {'User-Agent': cls.USER_AGENT}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract and normalize category data
            categories = []
            for tag in data.get('tags', []):
                if tag.get('products') > 100:  # Only include popular categories
                    categories.append({
                        'id': tag.get('id'),
                        'name': tag.get('name'),
                        'products': tag.get('products', 0),
                        'url': tag.get('url')
                    })
            
            # Sort by product count
            categories.sort(key=lambda x: x['products'], reverse=True)
            
            # Cache the results (longer time since categories rarely change)
            cache.set(cache_key, categories, CACHE_TIMEOUT * 7)  # Cache for a week
            
            return categories
            
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            return []
    
    @classmethod
    def _normalize_product_data(cls, product):
        """
        Normalize and extract relevant product data from API response.
        
        Args:
            product (dict): Raw product data from API
            
        Returns:
            dict: Normalized product data
        """
        # Extract nutrition data
        nutrition = product.get('nutriments', {})
        
        # Get the most appropriate image URL
        image_url = None
        selected_images = product.get('selected_images', {})
        if selected_images:
            # Try to get front image in various sizes
            front_images = selected_images.get('front', {})
            for size in ['display', 'small', 'thumb']:
                if front_images.get(size):
                    image_url = front_images[size].get('en')
                    if image_url:
                        break
        
        # Fallback to other image fields if needed
        if not image_url:
            for img_field in ['image_url', 'image_small_url', 'image_thumb_url']:
                if product.get(img_field):
                    image_url = product.get(img_field)
                    break
        
        # Extract and normalize allergens
        allergens = []
        if product.get('allergens_tags'):
            allergens = [a.replace('en:', '') for a in product.get('allergens_tags', [])]
        
        # Extract nutrient levels
        nutrient_levels = {}
        if product.get('nutrient_levels'):
            for nutrient, level in product.get('nutrient_levels', {}).items():
                if nutrient in ['fat', 'salt', 'sugars', 'saturated-fat']:
                    nutrient_levels[nutrient] = level
        
        # Determine a main category
        main_category = None
        if product.get('categories_hierarchy'):
            # Try to get a mid-level category (not too generic, not too specific)
            categories = product.get('categories_hierarchy', [])
            if len(categories) >= 3:
                main_category = categories[2].replace('en:', '')
            elif len(categories) >= 2:
                main_category = categories[1].replace('en:', '')
            elif len(categories) >= 1:
                main_category = categories[0].replace('en:', '')
        
        # Ensure category is properly formatted
        if main_category:
            main_category = main_category.replace('-', ' ').title()
        
        # Create normalized product object
        normalized_product = {
            'code': product.get('code', ''),
            'name': product.get('product_name', ''),
            'brand': product.get('brands', ''),
            'category': main_category,
            'image_url': image_url,
            'quantity': product.get('quantity', ''),
            'ingredients': product.get('ingredients_text', ''),
            'allergens': allergens,
            'nutrient_levels': nutrient_levels,
            'nutrition_data': {
                'energy': nutrition.get('energy-kcal_100g'),
                'fat': nutrition.get('fat_100g'),
                'saturated_fat': nutrition.get('saturated-fat_100g'),
                'carbohydrates': nutrition.get('carbohydrates_100g'),
                'sugars': nutrition.get('sugars_100g'),
                'protein': nutrition.get('proteins_100g'),
                'salt': nutrition.get('salt_100g'),
                'fiber': nutrition.get('fiber_100g'),
            },
            'nutriscore': product.get('nutriscore_grade'),
            'ecoscore': product.get('ecoscore_grade'),
            'packaging': product.get('packaging', ''),
            'origin': product.get('origins', ''),
            'stores': product.get('stores', '').split(',') if product.get('stores') else [],
            'countries': product.get('countries', '').split(',') if product.get('countries') else [],
            'ingredients_analysis': product.get('ingredients_analysis_tags', []),
            'last_modified': product.get('last_modified_t', 0),
        }
        
        # Clean up empty values
        for key, value in list(normalized_product.items()):
            if value is None or value == '' or (isinstance(value, list) and len(value) == 0) or (isinstance(value, dict) and len(value) == 0):
                normalized_product[key] = None
                
        return normalized_product