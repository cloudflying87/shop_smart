from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages

from shopping.models import (
    Family, FamilyMember, UserProfile, GroceryStore, StoreLocation,
    ProductCategory, GroceryItem, ShoppingList, ShoppingListItem
)


class HomeViewTests(TestCase):
    """Tests for the home view"""
    
    def setUp(self):
        self.client = Client()
        self.home_url = reverse('landing')
        
    def test_home_view_unauthenticated(self):
        """Test that the home view redirects unauthenticated users to login page"""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login page
        
        # Verify redirect path starts with the login URL (exact redirect URL may include next param)
        self.assertTrue(response.url.startswith(reverse('login')))


class DashboardViewTests(TestCase):
    """Tests for the dashboard view"""
    
    def setUp(self):
        self.client = Client()
        self.dashboard_url = reverse('groceries:dashboard')
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create a family
        self.family = Family.objects.create(
            name='Test Family',
            created_by=self.user
        )
        
        # Add user to family
        self.family_member = FamilyMember.objects.create(
            user=self.user,
            family=self.family,
            is_admin=True
        )
        
        # Set as default family
        self.profile = UserProfile.objects.get(user=self.user)
        self.profile.default_family = self.family
        self.profile.save()
        
        # Create a store
        self.store = GroceryStore.objects.create(name='Test Store')
        
        # Create shopping lists
        self.active_list = ShoppingList.objects.create(
            name='Active List',
            store=self.store,
            family=self.family,
            created_by=self.user
        )
        
        self.completed_list = ShoppingList.objects.create(
            name='Completed List',
            store=self.store,
            family=self.family,
            created_by=self.user,
            completed=True
        )
        
    def test_dashboard_view_unauthenticated(self):
        """Test that the dashboard view redirects unauthenticated users to login page"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login page
        
    def test_dashboard_view_authenticated(self):
        """Test that authenticated users can access the dashboard"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        
        # Check context data
        self.assertIn('recent_lists', response.context)
        self.assertIn('family', response.context)

        # Verify the recent lists include both lists
        self.assertEqual(len(response.context['recent_lists']), 2)

        # Check that both lists are included in recent_lists
        recent_list_ids = [list_obj.id for list_obj in response.context['recent_lists']]
        self.assertIn(self.active_list.id, recent_list_ids)
        self.assertIn(self.completed_list.id, recent_list_ids)


class ShoppingListViewTests(TestCase):
    """Tests for the shopping list views"""
    
    def setUp(self):
        self.client = Client()
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create a family
        self.family = Family.objects.create(
            name='Test Family',
            created_by=self.user
        )
        
        # Add user to family
        self.family_member = FamilyMember.objects.create(
            user=self.user,
            family=self.family,
            is_admin=True
        )
        
        # Set as default family
        self.profile = UserProfile.objects.get(user=self.user)
        self.profile.default_family = self.family
        self.profile.save()
        
        # Create a store
        self.store = GroceryStore.objects.create(name='Test Store')
        
        # Create a category
        self.category = ProductCategory.objects.create(name='Test Category')
        
        # Create grocery items
        self.item1 = GroceryItem.objects.create(
            name='Test Item 1',
            category=self.category,
            created_by=self.user
        )
        self.item2 = GroceryItem.objects.create(
            name='Test Item 2',
            category=self.category,
            created_by=self.user
        )
        
        # Create a shopping list
        self.shopping_list = ShoppingList.objects.create(
            name='Test List',
            store=self.store,
            family=self.family,
            created_by=self.user
        )
        
        # Add items to the list
        self.list_item = ShoppingListItem.objects.create(
            shopping_list=self.shopping_list,
            item=self.item1,
            quantity=1
        )
        
        # URLs
        self.list_create_url = reverse('groceries:create_list')
        self.list_detail_url = reverse('groceries:list_detail', args=[self.shopping_list.id])
        self.list_edit_url = reverse('groceries:edit_list', args=[self.shopping_list.id])
        self.list_delete_url = reverse('groceries:delete_list', args=[self.shopping_list.id])
        
    def test_list_create_view(self):
        """Test the shopping list creation view"""
        self.client.login(username='testuser', password='testpassword')
        
        # Test GET request
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'groceries/lists/create.html')
        
        # Test POST request
        post_data = {
            'name': 'New Shopping List',
            'store': self.store.id,
            'family': self.family.id
        }
        response = self.client.post(self.list_create_url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Check that the list was created
        new_list = ShoppingList.objects.filter(name='New Shopping List').first()
        self.assertIsNotNone(new_list)
        self.assertEqual(new_list.store.id, self.store.id)
        self.assertEqual(new_list.family.id, self.family.id)
        self.assertEqual(new_list.created_by, self.user)
        
    def test_list_detail_view(self):
        """Test the shopping list detail view"""
        self.client.login(username='testuser', password='testpassword')
        
        response = self.client.get(self.list_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'groceries/lists/detail.html')
        
        # Check context data
        self.assertEqual(response.context['shopping_list'], self.shopping_list)
        self.assertIn('list_items', response.context)
        self.assertEqual(len(response.context['list_items']), 1)
        self.assertEqual(response.context['list_items'][0], self.list_item)
        
    def test_list_edit_view(self):
        """Test the shopping list edit view"""
        self.client.login(username='testuser', password='testpassword')
        
        # Test GET request
        response = self.client.get(self.list_edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'groceries/lists/edit.html')
        
        # Test POST request
        post_data = {
            'name': 'Updated Shopping List',
            'store': self.store.id,
            'family': self.family.id
        }
        response = self.client.post(self.list_edit_url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Check that the list was updated
        self.shopping_list.refresh_from_db()
        self.assertEqual(self.shopping_list.name, 'Updated Shopping List')
        
    def test_list_delete_view(self):
        """Test the shopping list delete view"""
        self.client.login(username='testuser', password='testpassword')
        
        # Test GET request (confirmation page)
        response = self.client.get(self.list_delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'groceries/lists/confirm_delete.html')
        
        # Test POST request (actual deletion)
        response = self.client.post(self.list_delete_url, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Check that the list was deleted
        with self.assertRaises(ShoppingList.DoesNotExist):
            ShoppingList.objects.get(id=self.shopping_list.id)


class ItemManagementViewTests(TestCase):
    """Tests for the item management views"""
    
    def setUp(self):
        self.client = Client()
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Create a family
        self.family = Family.objects.create(
            name='Test Family',
            created_by=self.user
        )
        
        # Add user to family
        self.family_member = FamilyMember.objects.create(
            user=self.user,
            family=self.family,
            is_admin=True
        )
        
        # Create a store
        self.store = GroceryStore.objects.create(name='Test Store')
        
        # Create a category
        self.category = ProductCategory.objects.create(name='Test Category')
        
        # Create a shopping list
        self.shopping_list = ShoppingList.objects.create(
            name='Test List',
            store=self.store,
            family=self.family,
            created_by=self.user
        )
        
        # Create grocery items
        self.item = GroceryItem.objects.create(
            name='Test Item',
            category=self.category,
            created_by=self.user
        )
        
        # URLs
        self.item_add_url = reverse('groceries:add_list_item', args=[self.shopping_list.id])
        
    def test_item_add_view(self):
        """Test adding an item to a shopping list"""
        self.client.login(username='testuser', password='testpassword')
        
        # Test GET request
        response = self.client.get(self.item_add_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'groceries/items/create.html')
        
        # Test POST request with existing item
        post_data = {
            'item_id': self.item.id,
            'quantity': 2,
            'unit': 'kg',
            'note': 'Test note'
        }
        response = self.client.post(self.item_add_url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Check that the item was added to the list
        list_item = ShoppingListItem.objects.filter(
            shopping_list=self.shopping_list,
            item=self.item
        ).first()
        self.assertIsNotNone(list_item)
        self.assertEqual(list_item.quantity, 2)
        self.assertEqual(list_item.unit, 'kg')
        self.assertEqual(list_item.note, 'Test note')
        
        # Test creating a new item and adding it to the list
        post_data = {
            'name': 'New Item',
            'category': self.category.id,
            'quantity': 1,
            'unit': 'piece',
            'note': 'Another test note'
        }
        response = self.client.post(self.item_add_url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Check that a new item was created
        new_item = GroceryItem.objects.filter(name='New Item').first()
        self.assertIsNotNone(new_item)
        
        # Check that the new item was added to the list
        list_item = ShoppingListItem.objects.filter(
            shopping_list=self.shopping_list,
            item=new_item
        ).first()
        self.assertIsNotNone(list_item)
        self.assertEqual(list_item.quantity, 1)
        self.assertEqual(list_item.unit, 'piece')
        self.assertEqual(list_item.note, 'Another test note')