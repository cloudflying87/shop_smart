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

        Args:
            family: The Family object to generate recommendations for
            store: Optional GroceryStore to filter recommendations by
            limit: Maximum number of recommendations to return

        Returns:
            QuerySet of recommended GroceryItems
        """
        from .models import GroceryItem, ShoppingList, ShoppingListItem, FamilyItemUsage

        try:
            # Base recommendations on family's purchase history
            recommendations = cls._get_family_favorites(family, store, limit)
            
            # If we don't have enough recommendations, add seasonal items
            if recommendations.count() < limit:
                seasonal_items = cls._get_seasonal_recommendations(store, limit - recommendations.count())
                recommendation_ids = list(recommendations.values_list('id', flat=True))
                seasonal_items = seasonal_items.exclude(id__in=recommendation_ids)
                recommendations = recommendations | seasonal_items
            
            # Add items that might need replenishment based on purchase frequency
            if recommendations.count() < limit:
                replenishment_items = cls._get_replenishment_suggestions(family, store, limit - recommendations.count())
                recommendation_ids = list(recommendations.values_list('id', flat=True))
                replenishment_items = replenishment_items.exclude(id__in=recommendation_ids)
                recommendations = recommendations | replenishment_items
            
            # If still not enough, add collaborative filtering recommendations
            if recommendations.count() < limit:
                collaborative_items = cls._get_collaborative_recommendations(family, store, limit - recommendations.count())
                recommendation_ids = list(recommendations.values_list('id', flat=True))
                collaborative_items = collaborative_items.exclude(id__in=recommendation_ids)
                recommendations = recommendations | collaborative_items

            # Order by relevance and limit
            recommendations = recommendations.order_by('-global_popularity')[:limit]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations for family {family.id}: {str(e)}")
            # Fallback to basic recommendations
            if store:
                return GroceryItem.objects.filter(
                    store_info__store=store
                ).order_by('-global_popularity')[:limit]
            return GroceryItem.objects.order_by('-global_popularity')[:limit]
    
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
            if not shopping_list.items.exists():
                # If list is empty, fall back to family recommendations
                return cls.get_recommendations_for_family(
                    shopping_list.family, 
                    shopping_list.store, 
                    limit
                )
            
            # Get items already in the list
            existing_items = shopping_list.items.values_list('item_id', flat=True)
            
            # Get common co-purchased items from this family's history
            family = shopping_list.family
            list_items = list(existing_items)
            
            # Find items that are frequently purchased with items in this list
            co_purchased = cls._get_co_purchased_items(
                family, 
                list_items, 
                store=shopping_list.store,
                limit=limit
            )
            
            # If we don't have enough suggestions, add recipe-based complements
            if co_purchased.count() < limit:
                recipe_items = cls._get_recipe_complements(
                    list_items,
                    store=shopping_list.store,
                    limit=limit - co_purchased.count()
                )
                # Exclude items already recommended
                co_purchased_ids = list(co_purchased.values_list('id', flat=True))
                recipe_items = recipe_items.exclude(id__in=co_purchased_ids + list_items)
                
                recommendations = co_purchased | recipe_items
            else:
                recommendations = co_purchased
            
            # Ensure we're not recommending items already in the list
            recommendations = recommendations.exclude(id__in=existing_items)
            
            # Order by relevance and limit
            recommendations = recommendations.order_by('-global_popularity')[:limit]
            
            return recommendations
            
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
            12: ['Christmas', 'Winter', 'Holiday'],
            1: ['Winter Foods', 'Soups', 'Hot Beverages'],
            2: ['Winter Foods', 'Valentine', 'Chocolate'],
            
            # Spring
            3: ['Spring', 'Easter', 'Gardening'],
            4: ['Spring Foods', 'Fresh Produce', 'Salads'],
            5: ['Picnic', 'Barbecue', 'Outdoor'],
            
            # Summer
            6: ['Summer', 'Barbecue', 'Ice Cream'],
            7: ['Summer Foods', 'Grilling', 'Cold Beverages'],
            8: ['Summer Foods', 'Salads', 'Refreshments'],
            
            # Fall
            9: ['Back to School', 'Fall Foods', 'Baking'],
            10: ['Fall', 'Halloween', 'Pumpkin'],
            11: ['Thanksgiving', 'Fall', 'Baking'],
        }
        
        # Get categories for current month
        current_categories = seasonal_categories.get(current_month, [])
        
        # Query items with these categories
        seasonal_items = GroceryItem.objects.filter(
            category__name__in=current_categories
        ).order_by('-global_popularity')
        
        # Filter by store if specified
        if store:
            seasonal_items = seasonal_items.filter(store_info__store=store)
            
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
            shopping_list_items__shopping_list__in=lists_with_items
        ).exclude(
            id__in=item_ids
        ).annotate(
            purchase_count=Count('shopping_list_items')
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
        
        # Get categories of the items
        item_categories = list(GroceryItem.objects.filter(
            id__in=item_ids,
            category__isnull=False
        ).values_list('category_id', flat=True).distinct())
        
        # Define some basic recipe/pairing relationships
        recipe_pairings = {
            'Meat': ['Marinade', 'BBQ Sauce', 'Spices'],
            'Pasta': ['Pasta Sauce', 'Cheese', 'Herbs'],
            'Bread': ['Butter', 'Jam', 'Sandwich Filling'],
            'Dairy': ['Cereal', 'Coffee', 'Tea'],
            'Vegetables': ['Salad Dressing', 'Dips', 'Herbs'],
            'Fruit': ['Yogurt', 'Cream', 'Honey'],
        }
        
        # Find items in complementary categories
        complementary_categories = []
        
        for category_id in item_categories:
            try:
                category = ProductCategory.objects.get(id=category_id)
                for main_category, complements in recipe_pairings.items():
                    if main_category.lower() in category.name.lower():
                        complementary_categories.extend(complements)
            except ProductCategory.DoesNotExist:
                pass
        
        # Query items in complementary categories
        complementary_items = GroceryItem.objects.filter(
            category__name__in=complementary_categories
        ).order_by('-global_popularity')
        
        # Filter by store if specified
        if store:
            complementary_items = complementary_items.filter(store_info__store=store)
            
        return complementary_items[:limit]