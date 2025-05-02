from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import mock

from shopping.models import (
    Family, GroceryStore, ProductCategory, GroceryItem, 
    ShoppingList, ShoppingListItem, FamilyItemUsage
)
from shopping.recommender import ShoppingRecommender


class ShoppingRecommenderTests(TestCase):
    """Tests for the shopping recommender system"""
    
    def setUp(self):
        # Create a test user and family
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.family = Family.objects.create(
            name='Test Family',
            created_by=self.user
        )
        
        # Create a store
        self.store = GroceryStore.objects.create(name='Test Store')
        
        # Create categories
        self.dairy_category = ProductCategory.objects.create(name='Dairy')
        self.meat_category = ProductCategory.objects.create(name='Meat')
        self.produce_category = ProductCategory.objects.create(name='Produce')
        self.winter_category = ProductCategory.objects.create(name='Winter Foods')
        
        # Create grocery items
        self.milk = GroceryItem.objects.create(
            name='Milk',
            category=self.dairy_category,
            created_by=self.user,
            global_popularity=10
        )
        self.eggs = GroceryItem.objects.create(
            name='Eggs',
            category=self.dairy_category,
            created_by=self.user,
            global_popularity=8
        )
        self.cheese = GroceryItem.objects.create(
            name='Cheese',
            category=self.dairy_category,
            created_by=self.user,
            global_popularity=6
        )
        self.chicken = GroceryItem.objects.create(
            name='Chicken',
            category=self.meat_category,
            created_by=self.user,
            global_popularity=9
        )
        self.beef = GroceryItem.objects.create(
            name='Beef',
            category=self.meat_category,
            created_by=self.user,
            global_popularity=7
        )
        self.apples = GroceryItem.objects.create(
            name='Apples',
            category=self.produce_category,
            created_by=self.user,
            global_popularity=5
        )
        self.hot_cocoa = GroceryItem.objects.create(
            name='Hot Cocoa',
            category=self.winter_category,
            created_by=self.user,
            global_popularity=4
        )
        
        # Create family usage records
        FamilyItemUsage.objects.create(family=self.family, item=self.milk, usage_count=10)
        FamilyItemUsage.objects.create(family=self.family, item=self.eggs, usage_count=8)
        FamilyItemUsage.objects.create(family=self.family, item=self.chicken, usage_count=6)
        
        # Create a shopping list
        self.shopping_list = ShoppingList.objects.create(
            name='Test List',
            store=self.store,
            family=self.family,
            created_by=self.user
        )
        
        # Add some items to the list
        ShoppingListItem.objects.create(
            shopping_list=self.shopping_list,
            item=self.milk,
            quantity=1
        )
        ShoppingListItem.objects.create(
            shopping_list=self.shopping_list,
            item=self.chicken,
            quantity=1
        )

    def test_get_family_favorites(self):
        """Test that the _get_family_favorites method returns the family's most purchased items"""
        favorites = ShoppingRecommender._get_family_favorites(self.family, limit=5)
        
        # Check that the items are returned in the correct order
        self.assertEqual(favorites[0], self.milk)
        self.assertEqual(favorites[1], self.eggs)
        self.assertEqual(favorites[2], self.chicken)
        
        # Check that the limit is respected
        self.assertEqual(favorites.count(), 3)  # Only 3 items have usage records

    @mock.patch('shopping.recommender.datetime')
    def test_seasonal_recommendations(self, mock_datetime):
        """Test that the _get_seasonal_recommendations method returns seasonal items"""
        # Mock the current month to January
        mock_datetime.now.return_value.month = 1
        
        # Create winter item
        winter_item = GroceryItem.objects.create(
            name='Hot Soup',
            category=self.winter_category,
            created_by=self.user,
            global_popularity=5
        )
        
        seasonal_items = ShoppingRecommender._get_seasonal_recommendations(limit=5)
        
        # Check that our winter item is in the recommendations
        self.assertIn(winter_item, seasonal_items)
        self.assertEqual(seasonal_items.count(), 2)  # Hot Soup and Hot Cocoa
        
        # Mock the current month to July (summer)
        mock_datetime.now.return_value.month = 7
        
        # Create summer category and item
        summer_category = ProductCategory.objects.create(name='Summer Foods')
        summer_item = GroceryItem.objects.create(
            name='Ice Cream',
            category=summer_category,
            created_by=self.user,
            global_popularity=5
        )
        
        seasonal_items = ShoppingRecommender._get_seasonal_recommendations(limit=5)
        
        # Check that our summer item is in the recommendations
        self.assertIn(summer_item, seasonal_items)
        
    def test_replenishment_suggestions(self):
        """Test that the _get_replenishment_suggestions method identifies items needing replenishment"""
        # Create completed shopping lists with dates
        thirty_days_ago = timezone.now() - timedelta(days=30)
        twenty_days_ago = timezone.now() - timedelta(days=20)
        ten_days_ago = timezone.now() - timedelta(days=10)
        
        # Create lists with dates (oldest to newest)
        list1 = ShoppingList.objects.create(
            name='Old List 1',
            store=self.store,
            family=self.family,
            created_by=self.user,
            completed=True,
            completed_at=thirty_days_ago
        )
        list2 = ShoppingList.objects.create(
            name='Old List 2',
            store=self.store,
            family=self.family,
            created_by=self.user,
            completed=True,
            completed_at=twenty_days_ago
        )
        list3 = ShoppingList.objects.create(
            name='Recent List',
            store=self.store,
            family=self.family,
            created_by=self.user,
            completed=True,
            completed_at=ten_days_ago
        )
        
        # Milk was purchased in all three lists (every 10 days)
        ShoppingListItem.objects.create(shopping_list=list1, item=self.milk, quantity=1)
        ShoppingListItem.objects.create(shopping_list=list2, item=self.milk, quantity=1)
        ShoppingListItem.objects.create(shopping_list=list3, item=self.milk, quantity=1)
        
        # Eggs purchased less frequently (20 day interval)
        ShoppingListItem.objects.create(shopping_list=list1, item=self.eggs, quantity=1)
        ShoppingListItem.objects.create(shopping_list=list3, item=self.eggs, quantity=1)
        
        # Mock current date to be 9 days after the last purchase (just before milk would be needed)
        with mock.patch('shopping.recommender.timezone.now') as mock_now:
            mock_now.return_value = ten_days_ago + timedelta(days=9)
            replenish_items = ShoppingRecommender._get_replenishment_suggestions(self.family, limit=5)
            
            # Milk should not yet be suggested (9 days passed out of 10 day average = 90%)
            self.assertEqual(replenish_items.count(), 0)
            
            # Move one more day forward (now at 100% of the average interval)
            mock_now.return_value = ten_days_ago + timedelta(days=10)
            replenish_items = ShoppingRecommender._get_replenishment_suggestions(self.family, limit=5)
            
            # Now milk should be suggested
            self.assertEqual(replenish_items.count(), 1)
            self.assertIn(self.milk, replenish_items)

    def test_get_recommendations_for_family(self):
        """Test the main family recommendation method"""
        # Mock the other recommendation methods to isolate testing
        with mock.patch.multiple('shopping.recommender.ShoppingRecommender',
                              _get_family_favorites=mock.DEFAULT,
                              _get_seasonal_recommendations=mock.DEFAULT,
                              _get_replenishment_suggestions=mock.DEFAULT,
                              _get_collaborative_recommendations=mock.DEFAULT) as mocks:
            
            # Set up return values for the mocked methods
            mocks['_get_family_favorites'].return_value = GroceryItem.objects.filter(pk=self.milk.pk)
            mocks['_get_seasonal_recommendations'].return_value = GroceryItem.objects.filter(pk=self.hot_cocoa.pk)
            mocks['_get_replenishment_suggestions'].return_value = GroceryItem.objects.filter(pk=self.eggs.pk)
            mocks['_get_collaborative_recommendations'].return_value = GroceryItem.objects.filter(pk=self.cheese.pk)
            
            # Get recommendations
            recommendations = ShoppingRecommender.get_recommendations_for_family(self.family, limit=10)
            
            # Check that all methods were called
            mocks['_get_family_favorites'].assert_called_once_with(self.family, None, 10)
            mocks['_get_seasonal_recommendations'].assert_called_once()
            mocks['_get_replenishment_suggestions'].assert_called_once()
            mocks['_get_collaborative_recommendations'].assert_called_once()
            
            # Check that the recommendations include items from all methods
            self.assertEqual(recommendations.count(), 4)
            self.assertIn(self.milk, recommendations)
            self.assertIn(self.hot_cocoa, recommendations)
            self.assertIn(self.eggs, recommendations)
            self.assertIn(self.cheese, recommendations)

    def test_get_recommendations_based_on_list(self):
        """Test the shopping list based recommendation method"""
        # Add some co-purchased items history
        old_list = ShoppingList.objects.create(
            name='Old List',
            store=self.store,
            family=self.family,
            created_by=self.user,
            completed=True
        )
        
        # When milk and chicken were purchased before, so were eggs and cheese
        ShoppingListItem.objects.create(shopping_list=old_list, item=self.milk, quantity=1)
        ShoppingListItem.objects.create(shopping_list=old_list, item=self.chicken, quantity=1)
        ShoppingListItem.objects.create(shopping_list=old_list, item=self.eggs, quantity=1)
        ShoppingListItem.objects.create(shopping_list=old_list, item=self.cheese, quantity=1)
        
        # Mock the co-purchased and recipe methods
        with mock.patch.multiple('shopping.recommender.ShoppingRecommender',
                              _get_co_purchased_items=mock.DEFAULT,
                              _get_recipe_complements=mock.DEFAULT) as mocks:
            
            # Set up return values
            mocks['_get_co_purchased_items'].return_value = GroceryItem.objects.filter(pk__in=[self.eggs.pk, self.cheese.pk])
            mocks['_get_recipe_complements'].return_value = GroceryItem.objects.filter(pk=self.beef.pk)
            
            # Get recommendations based on the current list
            recommendations = ShoppingRecommender.get_recommendations_based_on_list(self.shopping_list, limit=10)
            
            # Check that the methods were called with expected arguments
            list_item_ids = list(self.shopping_list.items.values_list('item_id', flat=True))
            mocks['_get_co_purchased_items'].assert_called_once_with(
                self.family, list_item_ids, store=self.store, limit=10)
            mocks['_get_recipe_complements'].assert_called_once()
            
            # Check that the recommendations are as expected
            self.assertEqual(recommendations.count(), 3)
            self.assertIn(self.eggs, recommendations)
            self.assertIn(self.cheese, recommendations)
            self.assertIn(self.beef, recommendations)
            
            # Items already in the list should not be recommended
            self.assertNotIn(self.milk, recommendations)
            self.assertNotIn(self.chicken, recommendations)
    
    def test_empty_list_recommendations(self):
        """Test recommendations for an empty shopping list"""
        # Create an empty shopping list
        empty_list = ShoppingList.objects.create(
            name='Empty List',
            store=self.store,
            family=self.family,
            created_by=self.user
        )
        
        # Mock the family recommendations method
        with mock.patch('shopping.recommender.ShoppingRecommender.get_recommendations_for_family') as mock_family_recs:
            mock_family_recs.return_value = GroceryItem.objects.filter(pk__in=[self.milk.pk, self.eggs.pk])
            
            # Get recommendations for the empty list
            recommendations = ShoppingRecommender.get_recommendations_based_on_list(empty_list, limit=5)
            
            # Should fall back to family recommendations
            mock_family_recs.assert_called_once_with(self.family, self.store, 5)
            self.assertEqual(recommendations.count(), 2)
            self.assertIn(self.milk, recommendations)
            self.assertIn(self.eggs, recommendations)