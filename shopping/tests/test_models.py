from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal

from shopping.models import (
    Family, FamilyMember, UserProfile, GroceryStore, StoreLocation,
    ProductCategory, GroceryItem, ShoppingList, ShoppingListItem,
    ItemStoreInfo, FamilyItemUsage
)


class FamilyModelTests(TestCase):
    """Tests for the Family model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.family = Family.objects.create(
            name='Test Family',
            created_by=self.user
        )
        
    def test_family_creation(self):
        """Test that a Family can be created"""
        self.assertEqual(self.family.name, 'Test Family')
        self.assertEqual(self.family.created_by, self.user)
        self.assertIsNotNone(self.family.created_at)
        
    def test_family_string_representation(self):
        """Test the string representation of a Family"""
        self.assertEqual(str(self.family), 'Test Family')
        
    def test_get_suggested_items(self):
        """Test the get_suggested_items method"""
        # Create a store
        store = GroceryStore.objects.create(name='Test Store')
        
        # Create a product category
        category = ProductCategory.objects.create(name='Test Category')
        
        # Create some grocery items
        item1 = GroceryItem.objects.create(
            name='Test Item 1',
            category=category,
            created_by=self.user,
            global_popularity=10
        )
        item2 = GroceryItem.objects.create(
            name='Test Item 2',
            category=category,
            created_by=self.user,
            global_popularity=5
        )
        
        # Associate items with store
        ItemStoreInfo.objects.create(item=item1, store=store)
        ItemStoreInfo.objects.create(item=item2, store=store)
        
        # Create usage records for the family
        FamilyItemUsage.objects.create(
            family=self.family,
            item=item1,
            usage_count=5
        )
        FamilyItemUsage.objects.create(
            family=self.family,
            item=item2,
            usage_count=10
        )
        
        # Test without store filter
        suggested_items = self.family.get_suggested_items()
        self.assertEqual(len(suggested_items), 2)
        # Item2 should be first because it has higher usage count
        self.assertEqual(suggested_items[0], item2)
        self.assertEqual(suggested_items[1], item1)
        
        # Test with store filter
        suggested_items = self.family.get_suggested_items(store=store)
        self.assertEqual(len(suggested_items), 2)
        self.assertEqual(suggested_items[0], item2)
        self.assertEqual(suggested_items[1], item1)


class FamilyMemberTests(TestCase):
    """Tests for the FamilyMember model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.family = Family.objects.create(
            name='Test Family',
            created_by=self.user
        )
        self.family_member = FamilyMember.objects.create(
            user=self.user,
            family=self.family,
            is_admin=True
        )
        
    def test_family_member_creation(self):
        """Test that a FamilyMember can be created"""
        self.assertEqual(self.family_member.user, self.user)
        self.assertEqual(self.family_member.family, self.family)
        self.assertTrue(self.family_member.is_admin)
        self.assertIsNotNone(self.family_member.joined_at)
        
    def test_family_member_string_representation(self):
        """Test the string representation of a FamilyMember"""
        expected_string = f"testuser (Test Family)"
        self.assertEqual(str(self.family_member), expected_string)


class UserProfileTests(TestCase):
    """Tests for the UserProfile model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        # Profile should be created automatically via signal
        self.profile = UserProfile.objects.get(user=self.user)
        
    def test_user_profile_creation(self):
        """Test that a UserProfile is created when a User is created"""
        self.assertEqual(self.profile.user, self.user)
        self.assertFalse(self.profile.dark_mode)
        self.assertIsNone(self.profile.default_family)
        
    def test_user_profile_string_representation(self):
        """Test the string representation of a UserProfile"""
        expected_string = f"Profile for testuser"
        self.assertEqual(str(self.profile), expected_string)
        
    def test_allergen_preferences(self):
        """Test setting and getting allergen preferences"""
        allergens = ['peanuts', 'shellfish', 'gluten']
        self.profile.set_allergens(allergens)
        
        # Test retrieval
        saved_allergens = self.profile.get_allergens()
        self.assertEqual(saved_allergens, allergens)
        
    def test_dietary_preferences(self):
        """Test setting and getting dietary preferences"""
        preferences = ['vegan', 'keto']
        self.profile.set_preferences(preferences)
        
        # Test retrieval
        saved_preferences = self.profile.get_preferences()
        self.assertEqual(saved_preferences, preferences)


class GroceryStoreTests(TestCase):
    """Tests for the GroceryStore model"""
    
    def setUp(self):
        self.store = GroceryStore.objects.create(
            name='Test Store',
            address='123 Test St',
            website='http://teststore.com'
        )
        
    def test_store_creation(self):
        """Test that a GroceryStore can be created"""
        self.assertEqual(self.store.name, 'Test Store')
        self.assertEqual(self.store.address, '123 Test St')
        self.assertEqual(self.store.website, 'http://teststore.com')
        self.assertEqual(self.store.slug, 'test-store')
        
    def test_store_string_representation(self):
        """Test the string representation of a GroceryStore"""
        self.assertEqual(str(self.store), 'Test Store')


class ProductCategoryTests(TestCase):
    """Tests for the ProductCategory model"""
    
    def setUp(self):
        self.parent_category = ProductCategory.objects.create(
            name='Food',
            sort_order=1
        )
        self.category = ProductCategory.objects.create(
            name='Dairy',
            parent=self.parent_category,
            sort_order=2,
            icon='milk'
        )
        
    def test_category_creation(self):
        """Test that a ProductCategory can be created"""
        self.assertEqual(self.category.name, 'Dairy')
        self.assertEqual(self.category.parent, self.parent_category)
        self.assertEqual(self.category.sort_order, 2)
        self.assertEqual(self.category.icon, 'milk')
        
    def test_category_string_representation(self):
        """Test the string representation of a ProductCategory"""
        self.assertEqual(str(self.category), 'Dairy')
        
    def test_category_full_path(self):
        """Test the full_path property"""
        self.assertEqual(self.parent_category.full_path, 'Food')
        self.assertEqual(self.category.full_path, 'Food > Dairy')
        
        # Add a third level
        subcategory = ProductCategory.objects.create(
            name='Yogurt',
            parent=self.category
        )
        self.assertEqual(subcategory.full_path, 'Food > Dairy > Yogurt')


class GroceryItemTests(TestCase):
    """Tests for the GroceryItem model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.category = ProductCategory.objects.create(name='Dairy')
        self.item = GroceryItem.objects.create(
            name='Milk',
            description='Fresh milk',
            category=self.category,
            created_by=self.user,
            barcode='1234567890',
            brand='Test Brand',
            image_url='http://example.com/milk.jpg',
            global_popularity=5
        )
        self.family = Family.objects.create(
            name='Test Family',
            created_by=self.user
        )
        
    def test_item_creation(self):
        """Test that a GroceryItem can be created"""
        self.assertEqual(self.item.name, 'Milk')
        self.assertEqual(self.item.description, 'Fresh milk')
        self.assertEqual(self.item.category, self.category)
        self.assertEqual(self.item.created_by, self.user)
        self.assertEqual(self.item.barcode, '1234567890')
        self.assertEqual(self.item.brand, 'Test Brand')
        self.assertEqual(self.item.image_url, 'http://example.com/milk.jpg')
        self.assertEqual(self.item.global_popularity, 5)
        
    def test_item_string_representation(self):
        """Test the string representation of a GroceryItem"""
        self.assertEqual(str(self.item), 'Milk')
        
    def test_increment_popularity(self):
        """Test the increment_popularity method"""
        # Test global popularity
        self.item.increment_popularity()
        self.assertEqual(self.item.global_popularity, 6)
        
        # Test family-specific popularity
        self.item.increment_popularity(family=self.family)
        self.assertEqual(self.item.global_popularity, 7)
        
        # Check that a FamilyItemUsage was created
        usage = FamilyItemUsage.objects.get(family=self.family, item=self.item)
        self.assertEqual(usage.usage_count, 1)
        
        # Increment again for the same family
        self.item.increment_popularity(family=self.family)
        usage.refresh_from_db()
        self.assertEqual(usage.usage_count, 2)


class ShoppingListTests(TestCase):
    """Tests for the ShoppingList model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.family = Family.objects.create(
            name='Test Family',
            created_by=self.user
        )
        self.store = GroceryStore.objects.create(name='Test Store')
        self.category = ProductCategory.objects.create(name='Dairy')
        
        # Create a shopping list
        self.shopping_list = ShoppingList.objects.create(
            name='Test List',
            store=self.store,
            family=self.family,
            created_by=self.user
        )
        
        # Create some items
        self.item1 = GroceryItem.objects.create(
            name='Milk',
            category=self.category,
            created_by=self.user
        )
        self.item2 = GroceryItem.objects.create(
            name='Eggs',
            category=self.category,
            created_by=self.user
        )
        
        # Add items to the list
        self.list_item1 = ShoppingListItem.objects.create(
            shopping_list=self.shopping_list,
            item=self.item1,
            quantity=1,
            unit='gallon'
        )
        self.list_item2 = ShoppingListItem.objects.create(
            shopping_list=self.shopping_list,
            item=self.item2,
            quantity=12,
            unit='count'
        )
        
    def test_shopping_list_creation(self):
        """Test that a ShoppingList can be created"""
        self.assertEqual(self.shopping_list.name, 'Test List')
        self.assertEqual(self.shopping_list.store, self.store)
        self.assertEqual(self.shopping_list.family, self.family)
        self.assertEqual(self.shopping_list.created_by, self.user)
        self.assertFalse(self.shopping_list.completed)
        self.assertIsNone(self.shopping_list.completed_at)
        
    def test_shopping_list_string_representation(self):
        """Test the string representation of a ShoppingList"""
        expected_prefix = f"Test List - Test Store"
        self.assertTrue(str(self.shopping_list).startswith(expected_prefix))
        
    def test_total_items(self):
        """Test the total_items property"""
        self.assertEqual(self.shopping_list.total_items, 2)
        
    def test_checked_items(self):
        """Test the checked_items property"""
        self.assertEqual(self.shopping_list.checked_items, 0)
        
        # Check one item
        self.list_item1.checked = True
        self.list_item1.save()
        
        self.assertEqual(self.shopping_list.checked_items, 1)
        
    def test_progress_percentage(self):
        """Test the progress_percentage property"""
        self.assertEqual(self.shopping_list.progress_percentage, 0)
        
        # Check one item
        self.list_item1.checked = True
        self.list_item1.save()
        
        self.assertEqual(self.shopping_list.progress_percentage, 50)
        
        # Check both items
        self.list_item2.checked = True
        self.list_item2.save()
        
        self.assertEqual(self.shopping_list.progress_percentage, 100)
        
    def test_duplicate(self):
        """Test the duplicate method"""
        duplicate = self.shopping_list.duplicate("Duplicate List")
        
        self.assertEqual(duplicate.name, "Duplicate List")
        self.assertEqual(duplicate.store, self.store)
        self.assertEqual(duplicate.family, self.family)
        self.assertEqual(duplicate.created_by, self.user)
        self.assertFalse(duplicate.completed)
        
        # Check that items were duplicated
        duplicated_items = duplicate.items.all()
        self.assertEqual(len(duplicated_items), 2)
        
        # Check that the duplicated items have the same properties
        milk_item = duplicated_items.filter(item=self.item1).first()
        self.assertEqual(milk_item.quantity, Decimal('1'))
        self.assertEqual(milk_item.unit, 'gallon')
        
        eggs_item = duplicated_items.filter(item=self.item2).first()
        self.assertEqual(eggs_item.quantity, Decimal('12'))
        self.assertEqual(eggs_item.unit, 'count')