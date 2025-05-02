from django.test import TestCase
from django.core.cache import cache
import mock
import json
from requests.exceptions import RequestException

from shopping.food_api import OpenFoodFactsAPI


class MockResponse:
    """Mocked requests.Response object"""
    
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        
    def json(self):
        return self.json_data
        
    def raise_for_status(self):
        if self.status_code != 200:
            raise RequestException(f"HTTP Error: {self.status_code}")


class OpenFoodFactsAPITests(TestCase):
    """Tests for the OpenFoodFactsAPI class"""
    
    def setUp(self):
        # Clear cache before each test
        cache.clear()
        
        # Sample product data for testing
        self.sample_product_data = {
            "status": 1,
            "product": {
                "code": "123456789012",
                "product_name": "Test Product",
                "brands": "Test Brand",
                "quantity": "500g",
                "ingredients_text": "Ingredient 1, Ingredient 2, Ingredient 3",
                "allergens_tags": ["en:milk", "en:nuts"],
                "nutriments": {
                    "energy-kcal_100g": 250,
                    "fat_100g": 10,
                    "saturated-fat_100g": 5,
                    "carbohydrates_100g": 30,
                    "sugars_100g": 20,
                    "proteins_100g": 5,
                    "salt_100g": 1,
                    "fiber_100g": 2
                },
                "nutriscore_grade": "C",
                "ecoscore_grade": "B",
                "categories_hierarchy": ["en:food", "en:dairy", "en:cheese"],
                "image_url": "https://example.com/image.jpg",
                "stores": "Store A, Store B",
                "countries": "United States, Canada",
                "last_modified_t": 1609459200
            }
        }
        
        # Sample search data for testing
        self.sample_search_data = {
            "count": 2,
            "page": 1,
            "page_size": 20,
            "page_count": 1,
            "products": [
                {
                    "code": "123456789012",
                    "product_name": "Test Product 1",
                    "brands": "Test Brand",
                    "categories_hierarchy": ["en:food", "en:dairy", "en:cheese"],
                    "image_url": "https://example.com/image1.jpg"
                },
                {
                    "code": "123456789013",
                    "product_name": "Test Product 2",
                    "brands": "Another Brand",
                    "categories_hierarchy": ["en:food", "en:dairy", "en:yogurt"],
                    "image_url": "https://example.com/image2.jpg"
                }
            ]
        }
        
        # Sample categories data for testing
        self.sample_categories_data = {
            "tags": [
                {
                    "id": "en:dairy",
                    "name": "Dairy",
                    "products": 1000,
                    "url": "https://world.openfoodfacts.org/category/dairy"
                },
                {
                    "id": "en:meat",
                    "name": "Meat",
                    "products": 800,
                    "url": "https://world.openfoodfacts.org/category/meat"
                },
                {
                    "id": "en:very-specific-category",
                    "name": "Very Specific Category",
                    "products": 50,
                    "url": "https://world.openfoodfacts.org/category/very-specific-category"
                }
            ]
        }
    
    @mock.patch('shopping.food_api.requests.get')
    def test_get_product_success(self, mock_get):
        """Test successful product retrieval"""
        # Configure mock
        mock_get.return_value = MockResponse(self.sample_product_data)
        
        # Call the API method
        product = OpenFoodFactsAPI.get_product("123456789012")
        
        # Check that the request was made correctly
        mock_get.assert_called_once_with(
            "https://world.openfoodfacts.org/api/v0/product/123456789012.json",
            headers={"User-Agent": OpenFoodFactsAPI.USER_AGENT},
            timeout=5
        )
        
        # Check returned data
        self.assertIsNotNone(product)
        self.assertEqual(product["code"], "123456789012")
        self.assertEqual(product["name"], "Test Product")
        self.assertEqual(product["brand"], "Test Brand")
        self.assertEqual(product["category"], "Cheese")
        self.assertEqual(product["allergens"], ["milk", "nuts"])
        self.assertEqual(product["nutrition_data"]["energy"], 250)
        
    @mock.patch('shopping.food_api.requests.get')
    def test_get_product_not_found(self, mock_get):
        """Test product not found"""
        # Configure mock
        mock_get.return_value = MockResponse({"status": 0, "code": "not found"})
        
        # Call the API method
        product = OpenFoodFactsAPI.get_product("nonexistent")
        
        # Check that the request was made correctly
        mock_get.assert_called_once()
        
        # Check that None is returned
        self.assertIsNone(product)
        
    @mock.patch('shopping.food_api.requests.get')
    def test_get_product_request_error(self, mock_get):
        """Test handling of request errors"""
        # Configure mock to raise an exception
        mock_get.side_effect = RequestException("Connection error")
        
        # Call the API method
        product = OpenFoodFactsAPI.get_product("123456789012")
        
        # Check that None is returned on error
        self.assertIsNone(product)
        
    @mock.patch('shopping.food_api.requests.get')
    def test_get_product_caching(self, mock_get):
        """Test that product data is cached"""
        # Configure mock
        mock_get.return_value = MockResponse(self.sample_product_data)
        
        # First call should make a request
        product1 = OpenFoodFactsAPI.get_product("123456789012")
        self.assertEqual(mock_get.call_count, 1)
        
        # Second call should use cache
        product2 = OpenFoodFactsAPI.get_product("123456789012")
        self.assertEqual(mock_get.call_count, 1)  # Should not have increased
        
        # Check that both calls returned the same data
        self.assertEqual(product1, product2)
        
    @mock.patch('shopping.food_api.requests.get')
    def test_search_products_success(self, mock_get):
        """Test successful product search"""
        # Configure mock
        mock_get.return_value = MockResponse(self.sample_search_data)
        
        # Call the API method
        results = OpenFoodFactsAPI.search_products("test", page=1, page_size=20)
        
        # Check that the request was made correctly
        mock_get.assert_called_once()
        
        # Check returned data
        self.assertEqual(results["total"], 2)
        self.assertEqual(results["page"], 1)
        self.assertEqual(results["page_size"], 20)
        self.assertEqual(len(results["products"]), 2)
        self.assertEqual(results["products"][0]["name"], "Test Product 1")
        self.assertEqual(results["products"][1]["name"], "Test Product 2")
        
    @mock.patch('shopping.food_api.requests.get')
    def test_search_products_with_filters(self, mock_get):
        """Test search with category and brand filters"""
        # Configure mock
        mock_get.return_value = MockResponse(self.sample_search_data)
        
        # Call the API method with filters
        results = OpenFoodFactsAPI.search_products(
            "test", 
            categories=["dairy"], 
            brands=["Test Brand"]
        )
        
        # Check that the request was made with correct parameters
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["search_terms"], "test")
        self.assertEqual(kwargs["params"]["tagtype_0"], "categories")
        self.assertEqual(kwargs["params"]["tag_0"], "dairy")
        self.assertEqual(kwargs["params"]["tagtype_1"], "brands")
        self.assertEqual(kwargs["params"]["tag_1"], "Test Brand")
        
    @mock.patch('shopping.food_api.requests.get')
    def test_search_products_error(self, mock_get):
        """Test handling of search errors"""
        # Configure mock to raise an exception
        mock_get.side_effect = RequestException("Connection error")
        
        # Call the API method
        results = OpenFoodFactsAPI.search_products("test")
        
        # Check that an empty result set is returned
        self.assertEqual(len(results["products"]), 0)
        self.assertEqual(results["total"], 0)
        
    @mock.patch('shopping.food_api.requests.get')
    def test_get_categories_success(self, mock_get):
        """Test successful category retrieval"""
        # Configure mock
        mock_get.return_value = MockResponse(self.sample_categories_data)
        
        # Call the API method
        categories = OpenFoodFactsAPI.get_categories()
        
        # Check that the request was made correctly
        mock_get.assert_called_once_with(
            "https://world.openfoodfacts.org/api/v0/categories.json",
            headers={"User-Agent": OpenFoodFactsAPI.USER_AGENT},
            timeout=10
        )
        
        # Check returned data
        self.assertEqual(len(categories), 2)  # Only categories with >100 products
        self.assertEqual(categories[0]["name"], "Dairy")
        self.assertEqual(categories[1]["name"], "Meat")
        
        # Check that categories are sorted by product count
        self.assertTrue(categories[0]["products"] >= categories[1]["products"])
        
    @mock.patch('shopping.food_api.requests.get')
    def test_get_categories_error(self, mock_get):
        """Test handling of category retrieval errors"""
        # Configure mock to raise an exception
        mock_get.side_effect = RequestException("Connection error")
        
        # Call the API method
        categories = OpenFoodFactsAPI.get_categories()
        
        # Check that an empty list is returned
        self.assertEqual(categories, [])
        
    def test_normalize_product_data(self):
        """Test product data normalization"""
        # Extract raw product data
        raw_product = self.sample_product_data["product"]
        
        # Normalize the data
        normalized = OpenFoodFactsAPI._normalize_product_data(raw_product)
        
        # Check basic data
        self.assertEqual(normalized["code"], "123456789012")
        self.assertEqual(normalized["name"], "Test Product")
        self.assertEqual(normalized["brand"], "Test Brand")
        
        # Check allergen normalization
        self.assertEqual(normalized["allergens"], ["milk", "nuts"])
        
        # Check category normalization
        self.assertEqual(normalized["category"], "Cheese")
        
        # Check nutrition data
        self.assertEqual(normalized["nutrition_data"]["energy"], 250)
        self.assertEqual(normalized["nutrition_data"]["fat"], 10)
        
        # Check store splitting
        self.assertEqual(normalized["stores"], ["Store A", "Store B"])
        
    def test_normalize_product_missing_data(self):
        """Test normalization with missing product data"""
        # Create product with minimal data
        minimal_product = {
            "code": "123456789012",
            "product_name": "Minimal Product"
        }
        
        # Normalize the data
        normalized = OpenFoodFactsAPI._normalize_product_data(minimal_product)
        
        # Check that required fields are present
        self.assertEqual(normalized["code"], "123456789012")
        self.assertEqual(normalized["name"], "Minimal Product")
        
        # Check that missing fields are None
        self.assertIsNone(normalized["category"])
        self.assertIsNone(normalized["allergens"])
        self.assertIsNone(normalized["brand"])