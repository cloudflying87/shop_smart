# ShopSmart Architecture Guide

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Database Schema](#database-schema)
4. [Models](#models)
5. [Views](#views)
6. [Templates](#templates)
7. [Static Files](#static-files)
8. [APIs](#apis)
9. [Recommendation System](#recommendation-system)
10. [PWA Features](#pwa-features)
11. [Offline Support](#offline-support)
12. [Open Food Facts Integration](#open-food-facts-integration)
13. [Development Guidelines](#development-guidelines)
14. [Deployment](#deployment)

## Overview

ShopSmart is a Progressive Web Application (PWA) designed to simplify grocery shopping. It allows users to create, manage, and share shopping lists with family members, track prices, and receive personalized recommendations based on shopping history.

**Key Features:**
- Family sharing of shopping lists
- Multiple store support with store-specific item locations
- Offline functionality with background sync
- Family-specific item recommendations
- Price tracking
- Dark mode
- Responsive design optimized for mobile devices

**Tech Stack:**
- Backend: Django
- Frontend: HTML, CSS, JavaScript
- Database: PostgreSQL
- Deployment: Docker with Cloudflared
- External API: Open Food Facts for product database

## System Architecture

ShopSmart follows a standard Django MVT (Model-View-Template) architecture with enhancements for PWA functionality.

```
ShopSmart/
├── manage.py
├── shopsmart/                # Project directory
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── groceries/                # Main app directory
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views/                # Views organized by feature
│   │   ├── __init__.py
│   │   ├── list_views.py
│   │   ├── store_views.py
│   │   ├── family_views.py
│   │   ├── item_views.py
│   │   └── api_views.py
│   ├── forms.py
│   ├── urls.py
│   ├── recommender.py        # Recommendation system
│   ├── utils.py              # Utility functions
│   ├── templatetags/         # Custom template tags
│   ├── management/           # Management commands
│   │   └── commands/
│   │       └── import_products.py
│   ├── templates/
│   │   └── groceries/
│   │       ├── base.html
│   │       ├── landing.html
│   │       ├── dashboard.html
│   │       ├── lists/
│   │       ├── stores/
│   │       ├── items/
│   │       └── family/
│   └── static/
│       ├── css/
│       ├── js/
│       └── img/
├── static/                   # Project-wide static files
│   ├── manifest.json
│   ├── service-worker.js
│   └── icons/
├── templates/                # Project-wide templates
│   ├── base.html
│   ├── registration/
│   └── 404.html
└── Dockerfile
```

## Database Schema

The database schema is designed to handle the complex relationships between users, families, items, stores, and shopping lists.

![Database Schema](https://example.com/db-schema.png)

### Core Entities

- **User**: Django's built-in user model
- **Family**: Group of users that share shopping lists
- **GroceryStore**: Stores where shopping occurs
- **ProductCategory**: Hierarchical categories for grocery items
- **GroceryItem**: Individual grocery products
- **ShoppingList**: Lists created by users for specific stores and families
- **StoreLocation**: Zones within stores (e.g., produce, dairy)

### Relationship Entities

- **FamilyMember**: Links users to families
- **FamilyItemUsage**: Tracks how often families use specific items
- **ItemStoreInfo**: Links items to stores with additional data
- **ShoppingListItem**: Items on a shopping list
- **SyncLog**: Tracks offline changes for synchronization

## Models

### Family and User Models

```python
class Family(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_families')
    
    def get_suggested_items(self, store=None, limit=20):
        """Get suggested items for this family based on purchase history"""
        # Implementation details in model definition
```

```python
class FamilyMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='family_memberships')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='members')
    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
```

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    default_family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True, blank=True, related_name='default_for_users')
    dark_mode = models.BooleanField(default=False)
```

### Store Models

```python
class GroceryStore(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    families = models.ManyToManyField(Family, related_name='stores', blank=True)
    logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    slug = models.SlugField(unique=True, max_length=100)
```

```python
class StoreLocation(models.Model):
    name = models.CharField(max_length=100)
    store = models.ForeignKey(GroceryStore, on_delete=models.CASCADE, related_name='locations')
    sort_order = models.IntegerField(default=0)
```

### Item Models

```python
class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    sort_order = models.IntegerField(default=0)
    icon = models.CharField(max_length=50, blank=True, null=True)
```

```python
class GroceryItem(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, related_name='items')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    global_popularity = models.IntegerField(default=0)
    
    # Open Food Facts fields
    barcode = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    off_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    # Community fields
    is_verified = models.BooleanField(default=False)
    is_user_added = models.BooleanField(default=False)
    
    # Many-to-many fields
    stores = models.ManyToManyField(GroceryStore, through='ItemStoreInfo', related_name='items')
    families = models.ManyToManyField(Family, through='FamilyItemUsage', related_name='used_items')
    
    def increment_popularity(self, family=None):
        """Increment the popularity counter when item is added to a list"""
        # Implementation details in model definition
```

```python
class FamilyItemUsage(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='item_usage')
    item = models.ForeignKey(GroceryItem, on_delete=models.CASCADE, related_name='family_usage')
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(auto_now=True)
```

```python
class ItemStoreInfo(models.Model):
    item = models.ForeignKey(GroceryItem, on_delete=models.CASCADE, related_name='store_info')
    store = models.ForeignKey(GroceryStore, on_delete=models.CASCADE)
    location = models.ForeignKey(StoreLocation, on_delete=models.SET_NULL, null=True, blank=True)
    typical_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    last_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    last_purchased = models.DateTimeField(null=True, blank=True)
    average_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
```

### Shopping List Models

```python
class ShoppingList(models.Model):
    name = models.CharField(max_length=100)
    store = models.ForeignKey(GroceryStore, on_delete=models.CASCADE, related_name='lists')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='lists')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_lists')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def duplicate(self, new_name=None):
        """Create a duplicate of this list"""
        # Implementation details in model definition
```

```python
class ShoppingListItem(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(GroceryItem, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    unit = models.CharField(max_length=20, blank=True, null=True)
    checked = models.BooleanField(default=False)
    actual_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)
```

### Sync Model

```python
class SyncLog(models.Model):
    OPERATION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    operation = models.CharField(max_length=20, choices=OPERATION_CHOICES)
    model_name = models.CharField(max_length=50)
    record_id = models.IntegerField(null=True)
    data = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
    synced = models.BooleanField(default=False)
    synced_at = models.DateTimeField(null=True, blank=True)
```

## Views

ShopSmart uses class-based views for most functionality, organized by feature. Below are some key views:

### List Management Views

```python
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'groceries/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_profile = self.request.user.profile
        family = user_profile.default_family
        
        if not family and self.request.user.family_memberships.exists():
            family = self.request.user.family_memberships.first().family
        
        if family:
            context['recent_lists'] = ShoppingList.objects.filter(
                family=family
            ).order_by('-created_at')[:5]
            
            context['suggested_items'] = ShoppingRecommender.get_recommendations_for_family(
                family, limit=8
            )
        
        context['stores'] = GroceryStore.objects.filter(
            families__in=self.request.user.family_memberships.values_list('family', flat=True)
        ).distinct()
        
        context['family'] = family
        
        return context
```

```python
class ShoppingListCreateView(LoginRequiredMixin, CreateView):
    model = ShoppingList
    form_class = ShoppingListForm
    template_name = 'groceries/lists/create.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
        
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        
        # Process template list if selected
        template_list_id = form.cleaned_data.get('template_list')
        
        response = super().form_valid(form)
        
        if template_list_id:
            self.duplicate_template_items(template_list_id)
        
        messages.success(self.request, f'Shopping list "{form.instance.name}" created successfully')
        return response
    
    def get_success_url(self):
        return reverse('groceries:list_detail', kwargs={'pk': self.object.pk})
    
    def duplicate_template_items(self, template_list_id):
        try:
            template_list = ShoppingList.objects.get(id=template_list_id)
            if template_list.family == self.object.family:
                for item in template_list.items.all():
                    ShoppingListItem.objects.create(
                        shopping_list=self.object,
                        item=item.item,
                        quantity=item.quantity,
                        unit=item.unit,
                        note=item.note,
                        sort_order=item.sort_order
                    )
        except ShoppingList.DoesNotExist:
            pass
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['families'] = Family.objects.filter(
            members__user=self.request.user
        ).distinct()
        
        context['stores'] = GroceryStore.objects.filter(
            families__in=context['families']
        ).distinct()
        
        context['recent_lists'] = ShoppingList.objects.filter(
            family__in=context['families']
        ).order_by('-created_at')[:10]
        
        return context
```

```python
class ShoppingListDetailView(LoginRequiredMixin, DetailView):
    model = ShoppingList
    template_name = 'groceries/lists/detail.html'
    context_object_name = 'shopping_list'
    
    def get_queryset(self):
        # Ensure user can only view lists from their families
        return ShoppingList.objects.filter(
            family__members__user=self.request.user
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get list items, ordered by store location and checked status
        context['list_items'] = self.object.items.select_related(
            'item', 'item__category'
        ).order_by(
            'checked', 
            F('item__store_info__location__sort_order').asc(nulls_last=True),
            'sort_order',
            'item__name'
        )
        
        # Get recommendations for additional items
        context['recommended_items'] = ShoppingRecommender.get_recommendations_based_on_previous_list(
            self.object.id, limit=8
        )
        
        return context
```

### Item Management Views

```python
class GroceryItemSearchView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        family_id = request.GET.get('family')
        store_id = request.GET.get('store')
        query = request.GET.get('query', '').strip()
        
        if not family_id:
            return JsonResponse({'error': 'Family ID is required'}, status=400)
        
        try:
            family = Family.objects.get(id=family_id)
            
            # Check if user belongs to this family
            if not request.user.family_memberships.filter(family=family).exists():
                return JsonResponse({'error': 'You do not have permission to access this family'}, status=403)
            
            store = None
            if store_id:
                store = GroceryStore.objects.get(id=store_id)
            
            if query:
                # Search for items by name/brand matching the query
                items = GroceryItem.objects.filter(
                    Q(name__icontains=query) | Q(brand__icontains=query)
                )
                
                if store:
                    items = items.filter(store_info__store=store)
                
                # Sort by family usage first, then global popularity
                items = items.annotate(
                    family_usage_count=Count(
                        'family_usage',
                        filter=Q(family_usage__family=family),
                        distinct=True
                    )
                ).order_by('-family_usage_count', '-global_popularity')[:20]
                
            else:
                # Get recommendations for this family and store
                items = ShoppingRecommender.get_recommendations_for_family(
                    family, store, limit=20
                )
            
            # Format response
            items_data = [{
                'id': item.id,
                'name': item.name,
                'brand': item.brand or '',
                'category': item.category.name if item.category else '',
                'image_url': item.image_url or '',
            } for item in items]
            
            return JsonResponse({'items': items_data})
            
        except (Family.DoesNotExist, GroceryStore.DoesNotExist):
            return JsonResponse({'error': 'Invalid family or store ID'}, status=400)
```

```python
class AddItemToListView(LoginRequiredMixin, View):
    def post(self, request, list_id, *args, **kwargs):
        try:
            shopping_list = ShoppingList.objects.get(id=list_id)
            
            # Check if user belongs to this family
            if not request.user.family_memberships.filter(family=shopping_list.family).exists():
                return JsonResponse({'error': 'You do not have permission to modify this list'}, status=403)
            
            item_id = request.POST.get('item_id')
            quantity = request.POST.get('quantity', 1)
            unit = request.POST.get('unit', '')
            note = request.POST.get('note', '')
            
            if not item_id:
                return JsonResponse({'error': 'Item ID is required'}, status=400)
            
            # Get the item
            item = GroceryItem.objects.get(id=item_id)
            
            # Add to list
            list_item = ShoppingListItem.objects.create(
                shopping_list=shopping_list,
                item=item,
                quantity=quantity,
                unit=unit,
                note=note
            )
            
            # Return the new item details
            return JsonResponse({
                'success': True,
                'item': {
                    'id': list_item.id,
                    'item_id': item.id,
                    'name': item.name,
                    'quantity': quantity,
                    'unit': unit,
                    'note': note
                }
            })
            
        except ShoppingList.DoesNotExist:
            return JsonResponse({'error': 'Shopping list not found'}, status=404)
        except GroceryItem.DoesNotExist:
            return JsonResponse({'error': 'Grocery item not found'}, status=404)
```

### Family Management Views

```python
class FamilyListView(LoginRequiredMixin, ListView):
    model = Family
    template_name = 'groceries/family/list.html'
    context_object_name = 'families'
    
    def get_queryset(self):
        return Family.objects.filter(
            members__user=self.request.user
        ).distinct()
```

```python
class FamilyCreateView(LoginRequiredMixin, CreateView):
    model = Family
    form_class = FamilyForm
    template_name = 'groceries/family/create.html'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Add current user as a family member and admin
        FamilyMember.objects.create(
            user=self.request.user,
            family=self.object,
            is_admin=True
        )
        
        messages.success(self.request, f'Family "{form.instance.name}" created successfully')
        return response
    
    def get_success_url(self):
        return reverse('groceries:family_detail', kwargs={'pk': self.object.pk})
```

### Store Management Views

```python
class StoreListView(LoginRequiredMixin, ListView):
    model = GroceryStore
    template_name = 'groceries/stores/list.html'
    context_object_name = 'stores'
    
    def get_queryset(self):
        return GroceryStore.objects.filter(
            families__members__user=self.request.user
        ).distinct()
```

```python
class StoreDetailView(LoginRequiredMixin, DetailView):
    model = GroceryStore
    template_name = 'groceries/stores/detail.html'
    context_object_name = 'store'
    
    def get_queryset(self):
        return GroceryStore.objects.filter(
            families__members__user=self.request.user
        ).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['locations'] = self.object.locations.all().order_by('sort_order')
        context['recent_lists'] = ShoppingList.objects.filter(
            family__members__user=self.request.user,
            store=self.object
        ).order_by('-created_at')[:5]
        
        return context
```

## Templates

The templates use a base.html file for consistent layout and styling across all pages. Key templates include:

### Base Template

The base.html template includes:
- Navigation bar with user menu
- Theme toggling (light/dark mode)
- Global modal component
- Footer with app installation prompt
- Service worker registration
- Common JavaScript utilities

### Core Templates

- **Landing Page**: Public page with app info and login/register links
- **Dashboard**: User's home screen with recent lists and recommendations
- **List Templates**:
  - List creation form
  - List detail view with items and controls
  - List summary view for quick access
- **Store Templates**:
  - Store listing
  - Store detail with location management
- **Family Templates**:
  - Family management
  - Family member management
- **Item Templates**:
  - Item search and selection
  - Item detail with price history

## Static Files

Static files are organized by type and purpose:

### CSS Files

- **base.css**: Core styling and variables
- **responsive.css**: Media queries for different screen sizes
- **dark-mode.css**: Dark theme styling

### JavaScript Files

- **app.js**: Core functionality and initialization
- **modal-handler.js**: Global modal component management
- **theme-manager.js**: Theme toggling and persistence
- **list-management.js**: Shopping list operations
- **offline-sync.js**: Offline data handling
- **service-worker-register.js**: PWA registration

## APIs

ShopSmart provides several API endpoints for client-side interactions:

### Item APIs

- **GET /api/items/search/**: Search for grocery items
- **POST /api/items/create/**: Create new grocery items
- **GET /api/items/{id}/**: Get item details

### List APIs

- **GET /api/lists/**: Get user's shopping lists
- **POST /api/lists/create/**: Create new shopping list
- **GET /api/lists/{id}/**: Get list details
- **POST /api/lists/{id}/items/add/**: Add item to list
- **POST /api/lists/{id}/items/{item_id}/toggle/**: Toggle item checked status
- **POST /api/lists/{id}/items/{item_id}/price/**: Update item price

### Family APIs

- **GET /api/families/**: Get user's families
- **POST /api/families/create/**: Create new family
- **POST /api/families/{id}/members/add/**: Add member to family

### Recommendation APIs

- **GET /api/recommendations/**: Get personalized recommendations
- **GET /api/recommendations/list/{id}/**: Get recommendations based on list

## Recommendation System

The recommendation system is implemented in the `ShoppingRecommender` class and provides personalized item suggestions.

### Key Features

1. **Family-Based Recommendations**: Prioritizes items a family buys frequently
2. **Context-Aware Suggestions**: Takes into account the store and recent lists
3. **Collaborative Filtering**: Suggests items that are commonly bought together
4. **Seasonal Recommendations**: Suggests items based on time of year

### Recommendation Methods

- `get_recommendations_for_family()`: Returns items based on family usage patterns
- `get_recommendations_based_on_previous_list()`: Suggests items commonly purchased with those on a reference list
- `build_family_suggestions()`: Creates a complete set of recommendations with multiple categories

## PWA Features

ShopSmart is implemented as a Progressive Web App (PWA) with the following features:

### Core PWA Components

- **Manifest File**: Defines app name, icons, and display preferences
- **Service Worker**: Handles caching and offline functionality
- **Install Prompt**: Allows users to add the app to their home screen

### Service Worker Functionality

- **Static Asset Caching**: Caches CSS, JS, and images for offline use
- **API Response Caching**: Caches API responses with appropriate strategies
- **Background Sync**: Queues changes made offline for later sync
- **Push Notifications**: Supports notifications for shared lists (optional)

## Offline Support

ShopSmart works offline through several mechanisms:

### Client-Side Storage

- **IndexedDB**: Stores shopping lists and items for offline access
- **LocalStorage**: Stores user preferences and settings

### Sync Strategy

1. **Optimistic Updates**: UI updates immediately, changes are queued
2. **Background Sync**: Service worker syncs changes when online
3. **Conflict Resolution**: Server-side logic resolves conflicts
4. **SyncLog**: Database table tracks pending changes

### Offline Features

- Create and edit shopping lists
- Check off items while shopping
- Add new items to lists
- Track prices
- View recommendations based on cached data

## Open Food Facts Integration

ShopSmart integrates with the Open Food Facts database to provide a comprehensive item catalog.

### Integration Methods

1. **Initial Data Import**: Management command to populate the database
2. **Dynamic Fetching**: API integration for on-demand item lookups
3. **Barcode Scanning**: Look up products by barcode (future feature)

### Import Process

The `import_products` management command:
1. Creates a category hierarchy
2. Fetches popular products by category
3. Filters by completeness score
4. Maps data to the local database structure

### Data Fields Used

- Product name and description
- Brand
- Category
- Barcode
- Image URL
- Nutritional information (future feature)

## Development Guidelines

### Code Organization

- **Models**: One model per entity, organized logically
- **Views**: Class-based views organized by feature
- **Templates**: Hierarchical organization with inheritance
- **Static Files**: Separate directories for CSS, JS, and images

### Naming Conventions

- **Models**: Singular nouns (e.g., `GroceryItem`)
- **Views**: Purpose-oriented naming (e.g., `ShoppingListCreateView`)
- **Templates**: Match view names (e.g., `list_detail.html`)
- **URLs**: Descriptive slugs (e.g., `/lists/create/`)

### Development Process

1. **Feature Branches**: Develop features in separate branches
2. **Tests**: Write tests for models, views, and integration
3. **Code Review**: Peer review before merging
4. **Documentation**: Update this guide with new features

## Deployment

ShopSmart is deployed using Docker with Cloudflared.

### Deployment Stack

- **Docker**: Containerization for consistent environments
- **PostgreSQL**: Production database
- **Nginx**: Web server for static files
- **Gunicorn**: WSGI server for Django
- **Cloudflared**: Secure tunnel for deployment

### Docker Setup

The repository includes a Dockerfile and docker-compose.yml for easy deployment.

### Environment Variables

Key environment variables for deployment:
- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (False in production)
- `ALLOWED_HOSTS`: List of allowed hosts
- `DATABASE_URL`: PostgreSQL connection string
- `CLOUDFLARE_TOKEN`: Cloudflared authentication token

### Deployment Process

1. Clone repository on server
2. Set environment variables
3. Build and start containers: `docker-compose up -d`
4. Run migrations: `docker-compose exec web python manage.py migrate`
5. Create superuser: `docker-compose exec web python manage.py createsuperuser`
6. Import initial data: `docker-compose exec web python manage.py import_products`

---

This architecture guide serves as the central reference for the ShopSmart application. It should be updated as new features are developed and existing components are refined.