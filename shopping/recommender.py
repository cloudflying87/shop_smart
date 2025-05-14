"""
ShopSmart Recommender System

This module provides intelligent product recommendations based on:
1. Family purchase history
2. Shopping list contents
3. Seasonal trends
4. Store-specific patterns
5. Collaborative filtering (similar families)
"""

from datetime import datetime, timedelta
from django.db.models import Count, F, Q, Sum
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class ShoppingRecommender:
    """Provides smart product recommendations for ShopSmart users"""
    
    @classmethod
    def get_recommendations_for_family(cls, family, store=None, limit=10):
        """
        Generate personalized recommendations for a family, optionally filtered by store.

        Uses:
        1. Family purchase history (most frequently bought items)
        2. Seasonal recommendations
        3. Items that need to be replenished based on purchase frequency
        4. Similar families' popular items
        5. Common essential items for new users

        Args:
            family: The Family object to generate recommendations for
            store: Optional GroceryStore to filter recommendations by
            limit: Maximum number of recommendations to return

        Returns:
            QuerySet of recommended GroceryItems
        """
        from .models import GroceryItem, ShoppingList, ShoppingListItem, FamilyItemUsage

        try:
            recommendations_list = []
            
            # Get the family's purchase history if any
            family_purchase_exists = FamilyItemUsage.objects.filter(family=family).exists()
            
            # Base recommendations on family's purchase history if they have any
            if family_purchase_exists:
                recommendations = cls._get_family_favorites(family, store, limit)
                recommendations_list = list(recommendations)
            
            # If we don't have enough recommendations, add seasonal items
            if len(recommendations_list) < limit:
                seasonal_items = cls._get_seasonal_recommendations(store, limit - len(recommendations_list))
                
                # Filter out duplicates
                recommendation_ids = {item.id for item in recommendations_list}
                filtered_seasonal = [item for item in seasonal_items if item.id not in recommendation_ids]
                
                # Combine recommendations
                recommendations_list.extend(filtered_seasonal)
            
            # Add items that might need replenishment based on purchase frequency
            # (only if family has purchase history)
            if family_purchase_exists and len(recommendations_list) < limit:
                replenishment_items = cls._get_replenishment_suggestions(family, store, limit - len(recommendations_list))
                
                # Filter out duplicates
                recommendation_ids = {item.id for item in recommendations_list}
                filtered_replenishment = [item for item in replenishment_items if item.id not in recommendation_ids]
                
                # Combine recommendations
                recommendations_list.extend(filtered_replenishment)
            
            # If still not enough and family has purchase history, add collaborative filtering recommendations
            if family_purchase_exists and len(recommendations_list) < limit:
                collaborative_items = cls._get_collaborative_recommendations(family, store, limit - len(recommendations_list))
                
                # Filter out duplicates
                recommendation_ids = {item.id for item in recommendations_list}
                filtered_collaborative = [item for item in collaborative_items if item.id not in recommendation_ids]
                
                # Combine recommendations
                recommendations_list.extend(filtered_collaborative)
                
            # For new users or if we still need more items, add common essential items
            if len(recommendations_list) < limit:
                # Define essential categories that most people need
                essential_categories = ['Dairy', 'Vegetables', 'Fruit', 'Meat', 'Bakery', 'Pantry']
                popular_essentials_query = GroceryItem.objects.filter(
                    category__name__in=essential_categories
                ).order_by('-global_popularity')
                
                # Filter by store if specified
                if store:
                    popular_essentials_query = popular_essentials_query.filter(store_info__store=store)
                
                # Get the popular essentials and exclude any items already in our recommendations
                recommendation_ids = {item.id for item in recommendations_list}
                popular_essentials = list(popular_essentials_query.exclude(
                    id__in=recommendation_ids
                )[:limit-len(recommendations_list)])
                
                # Add these to our recommendations
                recommendations_list.extend(popular_essentials)
            
            # For new users with completely empty recommendations, add essential grocery items
            if not recommendations_list:
                # Essential items that most people need regularly
                essential_items = ['Milk', 'Eggs', 'Bread', 'Butter', 'Cheese', 
                                  'Chicken', 'Beef', 'Rice', 'Pasta', 'Potatoes',
                                  'Onions', 'Tomatoes', 'Lettuce', 'Bananas', 'Apples']
                
                essential_query = GroceryItem.objects.filter(
                    name__in=essential_items
                ).order_by('-global_popularity')
                
                if store:
                    essential_query = essential_query.filter(store_info__store=store)
                
                recommendations_list.extend(list(essential_query[:limit]))
            
            # If still not enough, add popular items across the board
            if len(recommendations_list) < limit:
                popular_query = GroceryItem.objects.all().order_by('-global_popularity')
                
                if store:
                    popular_query = popular_query.filter(store_info__store=store)
                
                recommendation_ids = {item.id for item in recommendations_list}
                popular_items = list(popular_query.exclude(
                    id__in=recommendation_ids
                )[:limit-len(recommendations_list)])
                
                recommendations_list.extend(popular_items)

            # Sort by global popularity and limit
            recommendations_list.sort(key=lambda x: -x.global_popularity)
            recommendations_list = recommendations_list[:limit]
            
            # Return the compiled list - should never be empty
            return recommendations_list
            
        except Exception as e:
            logger.error(f"Error generating recommendations for family {family.id}: {str(e)}")
            # Fallback to basic recommendations
            if store:
                return list(GroceryItem.objects.filter(
                    store_info__store=store
                ).order_by('-global_popularity')[:limit])
            return list(GroceryItem.objects.order_by('-global_popularity')[:limit])
    
    @classmethod
    def get_recommendations_based_on_list(cls, shopping_list, limit=10):
        """
        Generate recommendations based on current items in a shopping list.

        Uses:
        1. Common co-purchased items
        2. Recipe-based complements
        3. Family preferences

        Args:
            shopping_list: The ShoppingList object to generate recommendations for
            limit: Maximum number of recommendations to return

        Returns:
            QuerySet of recommended GroceryItems
        """
        from .models import GroceryItem, FamilyItemUsage
        
        try:
            # Check if the shopping list has any items
            item_count = shopping_list.items.count()
            
            if item_count == 0:
                # If list is empty, fall back to family recommendations
                return cls.get_recommendations_for_family(
                    shopping_list.family, 
                    shopping_list.store, 
                    limit
                )
            
            # Get items already in the list
            existing_items = list(shopping_list.items.values_list('item_id', flat=True))
            
            # Get common co-purchased items from this family's history
            family = shopping_list.family
            
            # Find items that are frequently purchased with items in this list
            co_purchased = cls._get_co_purchased_items(
                family, 
                existing_items, 
                store=shopping_list.store,
                limit=limit
            )
            
            # Convert to list immediately to avoid the slice has been taken error
            co_purchased_list = list(co_purchased)
            
            # If we don't have enough suggestions, add recipe-based complements
            if len(co_purchased_list) < limit:
                co_purchased_ids = [item.id for item in co_purchased_list]
                remaining_limit = limit - len(co_purchased_list)
                
                # Get recipe-based complements, excluding items we already have
                recipe_items = cls._get_recipe_complements(
                    existing_items,
                    store=shopping_list.store,
                    limit=remaining_limit
                )
                
                # Convert to list and exclude items we already have in co_purchased_list
                recipe_items_list = []
                for item in recipe_items:
                    if item.id not in co_purchased_ids and item.id not in existing_items:
                        recipe_items_list.append(item)
                        if len(recipe_items_list) >= remaining_limit:
                            break
                
                # Combine recommendations
                all_recommendations = co_purchased_list + recipe_items_list
            else:
                all_recommendations = co_purchased_list
            
            # Ensure we're not recommending items already in the list (double check)
            all_recommendations = [item for item in all_recommendations if item.id not in existing_items]
            
            # Sort by global popularity
            all_recommendations.sort(key=lambda x: -x.global_popularity)
            
            # Limit to requested number
            return all_recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error generating recommendations for list {shopping_list.id}: {str(e)}")
            # Fallback to family recommendations
            return cls.get_recommendations_for_family(
                shopping_list.family, 
                shopping_list.store, 
                limit
            )

    @classmethod
    def _get_family_favorites(cls, family, store=None, limit=10):
        """Get family's most frequently purchased items"""
        from .models import GroceryItem, FamilyItemUsage
        
        # Start with most frequently purchased items by this family
        favorites = GroceryItem.objects.filter(
            family_usage__family=family
        ).annotate(
            usage_count=F('family_usage__usage_count')
        ).order_by('-usage_count')
        
        # Filter by store if specified
        if store:
            favorites = favorites.filter(store_info__store=store)
            
        return favorites[:limit]
    
    @classmethod
    def _get_seasonal_recommendations(cls, store=None, limit=5):
        """Get seasonal recommendations based on current month"""
        from .models import GroceryItem, ProductCategory
        
        # Get current month
        current_month = datetime.now().month
        
        # Define seasonal categories mapping (simplified example)
        seasonal_categories = {
            # Winter
            12: ['Christmas', 'Winter', 'Holiday', 'Meat', 'Baking'],
            1: ['Winter', 'Soups', 'Hot Beverages', 'Dairy', 'Meat'],
            2: ['Winter', 'Valentine', 'Chocolate', 'Dairy', 'Bakery'],
            
            # Spring
            3: ['Spring', 'Easter', 'Gardening', 'Vegetables', 'Bakery'],
            4: ['Spring', 'Fresh Produce', 'Salads', 'Vegetables', 'Fruit'],
            5: ['Picnic', 'Barbecue', 'Outdoor', 'Meat', 'Snacks'],
            
            # Summer
            6: ['Summer', 'Barbecue', 'Ice Cream', 'Beverages', 'Frozen'],
            7: ['Summer', 'Grilling', 'Cold Beverages', 'Fruit', 'Frozen'],
            8: ['Summer', 'Salads', 'Refreshments', 'Fruit', 'Vegetables'],
            
            # Fall
            9: ['Back to School', 'Fall', 'Baking', 'Snacks', 'Pantry'],
            10: ['Fall', 'Halloween', 'Pumpkin', 'Vegetables', 'Snacks'],
            11: ['Thanksgiving', 'Fall', 'Baking', 'Meat', 'Vegetables'],
        }
        
        # Get categories for current month
        current_categories = seasonal_categories.get(current_month, [])
        
        # First try exact category name matches
        seasonal_items = GroceryItem.objects.filter(
            category__name__in=current_categories
        ).order_by('-global_popularity')
        
        # If we don't have enough items, try partial matches using case-insensitive contains
        if seasonal_items.count() < limit:
            from django.db.models import Q
            
            # Build a Q object for each search term
            q_objects = Q()
            for category in current_categories:
                q_objects |= Q(category__name__icontains=category)
                
            # Combine with existing items
            seasonal_items_partial = GroceryItem.objects.filter(q_objects).exclude(
                id__in=seasonal_items.values_list('id', flat=True)
            ).order_by('-global_popularity')
            
            # Convert both to lists and combine
            seasonal_items = list(seasonal_items) + list(seasonal_items_partial)
        else:
            seasonal_items = list(seasonal_items)
        
        # If still not enough items, include popular items by category
        if len(seasonal_items) < limit:
            top_categories = ['Vegetables', 'Dairy', 'Meat', 'Bakery', 'Fruit', 'Snacks', 'Beverages']
            popular_items = GroceryItem.objects.filter(
                category__name__in=top_categories
            ).exclude(
                id__in=[item.id for item in seasonal_items]
            ).order_by('-global_popularity')[:limit-len(seasonal_items)]
            
            seasonal_items.extend(list(popular_items))
            
        # Filter by store if specified
        if store:
            store_id = store.id
            seasonal_items = [item for item in seasonal_items 
                             if item.store_info.filter(store_id=store_id).exists()]
            
        return seasonal_items[:limit]
    
    @classmethod
    def _get_replenishment_suggestions(cls, family, store=None, limit=5):
        """Suggest items that might need replenishment based on purchase frequency"""
        from .models import GroceryItem, ShoppingListItem, ShoppingList
        
        # Calculate average days between purchases for each item
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Get completed lists from the past month
        recent_lists = ShoppingList.objects.filter(
            family=family,
            completed=True,
            completed_at__gte=thirty_days_ago
        )
        
        # Get items from these lists with their purchase dates
        recent_items = ShoppingListItem.objects.filter(
            shopping_list__in=recent_lists
        ).select_related('shopping_list', 'item')
        
        # Group by item and calculate average interval
        item_purchase_dates = {}
        for list_item in recent_items:
            item_id = list_item.item_id
            purchase_date = list_item.shopping_list.completed_at
            
            if item_id not in item_purchase_dates:
                item_purchase_dates[item_id] = []
                
            item_purchase_dates[item_id].append(purchase_date)
        
        # Calculate average purchase interval and estimate replenishment date
        items_to_replenish = []
        today = timezone.now()
        
        for item_id, dates in item_purchase_dates.items():
            if len(dates) > 1:
                # Calculate average interval
                sorted_dates = sorted(dates)
                intervals = [(sorted_dates[i+1] - sorted_dates[i]).days 
                             for i in range(len(sorted_dates)-1)]
                
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    last_purchase = max(sorted_dates)
                    days_since_purchase = (today - last_purchase).days
                    
                    # If we're at least 80% through the average interval, suggest replenishment
                    if days_since_purchase >= (avg_interval * 0.8):
                        items_to_replenish.append(item_id)
        
        # Query these items
        replenishment_items = GroceryItem.objects.filter(id__in=items_to_replenish)
        
        # Filter by store if specified
        if store:
            replenishment_items = replenishment_items.filter(store_info__store=store)
            
        return replenishment_items.order_by('-global_popularity')[:limit]
    
    @classmethod
    def _get_collaborative_recommendations(cls, family, store=None, limit=5):
        """Get recommendations based on similar families' purchases"""
        from .models import Family, FamilyItemUsage, GroceryItem
        
        # Find other families with similar purchase patterns
        family_items = list(FamilyItemUsage.objects.filter(
            family=family
        ).values_list('item_id', flat=True))
        
        if not family_items:
            return GroceryItem.objects.none()
        
        # Find families who bought at least 3 of the same items
        similar_families = Family.objects.filter(
            item_usage__item_id__in=family_items
        ).exclude(
            id=family.id
        ).annotate(
            common_items=Count('item_usage__item_id', 
                           filter=Q(item_usage__item_id__in=family_items))
        ).filter(
            common_items__gte=3
        )
        
        # Get popular items from these families that this family hasn't bought
        collaborative_items = GroceryItem.objects.filter(
            family_usage__family__in=similar_families
        ).exclude(
            id__in=family_items
        ).annotate(
            popularity=Count('family_usage')
        ).order_by('-popularity')
        
        # Filter by store if specified
        if store:
            collaborative_items = collaborative_items.filter(store_info__store=store)
            
        return collaborative_items[:limit]
    
    @classmethod
    def _get_co_purchased_items(cls, family, item_ids, store=None, limit=10):
        """Find items that are frequently purchased together with the given items"""
        from .models import ShoppingList, ShoppingListItem, GroceryItem
        
        # Get all lists that contain at least one of the specified items
        lists_with_items = ShoppingList.objects.filter(
            family=family,
            items__item_id__in=item_ids
        )
        
        # Get items that frequently appear in these lists
        co_purchased = GroceryItem.objects.filter(
            shoppinglistitem__shopping_list__in=lists_with_items
        ).exclude(
            id__in=item_ids
        ).annotate(
            purchase_count=Count('shoppinglistitem')
        ).order_by('-purchase_count')
        
        # Filter by store if specified
        if store:
            co_purchased = co_purchased.filter(store_info__store=store)
            
        return co_purchased[:limit]
    
    @classmethod
    def _get_recipe_complements(cls, item_ids, store=None, limit=5):
        """
        Suggest complementary items based on common recipes
        
        This is a simplified implementation. In a real system, this would 
        connect to a recipe database or use more sophisticated food pairing logic.
        """
        from .models import GroceryItem, ProductCategory
        from django.db.models import Q
        
        # Get categories and names of the items
        items_with_categories = GroceryItem.objects.filter(
            id__in=item_ids,
            category__isnull=False
        ).select_related('category')
        
        # Create two lists - one for category IDs, one for item names
        item_categories = []
        item_names = []
        item_category_names = []
        
        for item in items_with_categories:
            item_categories.append(item.category_id)
            item_names.append(item.name.lower())
            if item.category:
                item_category_names.append(item.category.name.lower())
        
        # Define some basic recipe/pairing relationships (expanded)
        recipe_pairings = {
            'Meat': ['Marinade', 'BBQ Sauce', 'Spices', 'Vegetables', 'Potatoes', 'Rice'],
            'Beef': ['Potatoes', 'Onions', 'Mushrooms', 'Gravy', 'Spices', 'Vegetables'],
            'Chicken': ['Rice', 'Pasta', 'Vegetables', 'Herbs', 'Lemon', 'Garlic'],
            'Fish': ['Lemon', 'Herbs', 'Rice', 'Vegetables', 'Potatoes', 'Garlic'],
            'Pasta': ['Pasta Sauce', 'Cheese', 'Herbs', 'Garlic', 'Olive Oil', 'Mushrooms'],
            'Rice': ['Vegetables', 'Meat', 'Beans', 'Spices', 'Soy Sauce', 'Oil'],
            'Bread': ['Butter', 'Jam', 'Cheese', 'Sandwich Filling', 'Eggs', 'Milk'],
            'Dairy': ['Cereal', 'Coffee', 'Tea', 'Fruit', 'Bread', 'Eggs'],
            'Vegetables': ['Salad Dressing', 'Dips', 'Herbs', 'Olive Oil', 'Lemon', 'Meat'],
            'Fruit': ['Yogurt', 'Cream', 'Honey', 'Cereal', 'Ice Cream', 'Baking'],
            'Cereal': ['Milk', 'Fruit', 'Yogurt', 'Sugar', 'Honey', 'Coffee'],
            'Eggs': ['Bread', 'Cheese', 'Vegetables', 'Bacon', 'Milk', 'Butter'],
            'Potatoes': ['Butter', 'Meat', 'Cheese', 'Vegetables', 'Herbs', 'Milk'],
            'Bacon': ['Eggs', 'Bread', 'Cheese', 'Potatoes', 'Lettuce', 'Tomatoes'],
            'Coffee': ['Milk', 'Sugar', 'Creamer', 'Breakfast', 'Cereal', 'Pastries'],
            'Bakery': ['Butter', 'Jam', 'Coffee', 'Milk', 'Cheese', 'Fruit'],
            'Snacks': ['Beverages', 'Dips', 'Cheese', 'Fruit', 'Cookies', 'Crackers'],
            'Breakfast': ['Eggs', 'Milk', 'Bread', 'Cereal', 'Coffee', 'Fruit'],
            'Lunch': ['Bread', 'Sandwich Filling', 'Cheese', 'Vegetables', 'Soup', 'Fruit'],
            'Dinner': ['Meat', 'Vegetables', 'Pasta', 'Rice', 'Potatoes', 'Salad'],
            'Baking': ['Flour', 'Sugar', 'Butter', 'Eggs', 'Milk', 'Vanilla'],
            'Beverages': ['Snacks', 'Ice', 'Lemon', 'Lime', 'Sugar', 'Milk'],
        }
        
        # Create a mapping of common food items to complementary items
        food_pairs = {
            'milk': ['cereal', 'coffee', 'tea', 'cookies', 'cake mix'],
            'bread': ['butter', 'jam', 'cheese', 'eggs', 'peanut butter', 'lunch meat'],
            'pasta': ['pasta sauce', 'parmesan cheese', 'garlic', 'olive oil', 'tomatoes'],
            'rice': ['beans', 'vegetables', 'chicken', 'soy sauce', 'curry'],
            'eggs': ['bacon', 'bread', 'cheese', 'milk', 'butter', 'vegetables'],
            'chicken': ['rice', 'pasta', 'vegetables', 'potatoes', 'salad', 'spices'],
            'beef': ['potatoes', 'onions', 'mushrooms', 'garlic', 'vegetables'],
            'fish': ['lemon', 'rice', 'vegetables', 'potatoes', 'garlic', 'herbs'],
            'cheese': ['bread', 'crackers', 'wine', 'grapes', 'pasta', 'olives'],
            'apples': ['caramel', 'cinnamon', 'peanut butter', 'cheese', 'oats'],
            'peanut butter': ['jelly', 'bread', 'honey', 'bananas', 'crackers'],
            'lettuce': ['tomatoes', 'cucumbers', 'salad dressing', 'onions', 'carrots'],
            'tomatoes': ['onions', 'garlic', 'basil', 'pasta', 'mozzarella', 'olive oil'],
            'potatoes': ['butter', 'sour cream', 'cheese', 'bacon', 'milk', 'onions'],
            'onions': ['garlic', 'peppers', 'beef', 'olive oil', 'tomatoes'],
            'garlic': ['olive oil', 'onions', 'tomatoes', 'pasta', 'herbs'],
            'cereal': ['milk', 'bananas', 'berries', 'sugar', 'honey'],
            'coffee': ['milk', 'sugar', 'creamer', 'breakfast pastries', 'cookies'],
            'tea': ['honey', 'lemon', 'sugar', 'milk', 'cookies'],
        }
        
        # Find items in complementary categories
        complementary_categories = []
        
        # First try to find complements based on categories
        for category_id in item_categories:
            try:
                category = ProductCategory.objects.get(id=category_id)
                for main_category, complements in recipe_pairings.items():
                    if main_category.lower() in category.name.lower():
                        complementary_categories.extend(complements)
            except ProductCategory.DoesNotExist:
                pass
                
        # Also try to find complements based on item names
        direct_complements = []
        for item_name in item_names:
            for food, complements in food_pairs.items():
                if food in item_name or any(food in category for category in item_category_names):
                    direct_complements.extend(complements)
        
        # Create a combined query
        q_objects = Q()
        
        # Add category-based complements
        if complementary_categories:
            q_objects |= Q(category__name__in=complementary_categories)
            
        # Add direct name-based complements using name contains
        for complement in direct_complements:
            q_objects |= Q(name__icontains=complement)
        
        # If we have no complements to suggest, use popular basic items
        if not complementary_categories and not direct_complements:
            # Most common food categories
            popular_categories = [
                'Vegetables', 'Dairy', 'Meat', 'Bakery', 'Fruit', 
                'Snacks', 'Beverages', 'Pantry', 'Breakfast'
            ]
            query = GroceryItem.objects.filter(
                category__name__in=popular_categories
            ).exclude(id__in=item_ids).order_by('-global_popularity')
        else:
            # Query items matching our criteria, excluding items already in the list
            query = GroceryItem.objects.filter(q_objects).exclude(id__in=item_ids).order_by('-global_popularity')
        
        # Filter by store if specified
        if store:
            query = query.filter(store_info__store=store)
            
        # Convert to list immediately to avoid the "Cannot filter a query once a slice has been taken" error
        return list(query[:limit])