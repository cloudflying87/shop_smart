from django.urls import path
from . import views

app_name = 'groceries'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Shopping Lists
    path('lists/', views.ShoppingListListView.as_view(), name='lists'),
    path('lists/create/', views.ShoppingListCreateView.as_view(), name='create_list'),
    path('lists/<int:pk>/', views.ShoppingListDetailView.as_view(), name='list_detail'),
    path('lists/<int:pk>/edit/', views.ShoppingListUpdateView.as_view(), name='edit_list'),
    path('lists/<int:pk>/delete/', views.ShoppingListDeleteView.as_view(), name='delete_list'),
    path('lists/<int:pk>/complete/', views.ShoppingListCompleteView.as_view(), name='complete_list'),
    path('lists/<int:pk>/reopen/', views.ShoppingListReopenView.as_view(), name='reopen_list'),
    path('lists/<int:pk>/duplicate/', views.ShoppingListDuplicateView.as_view(), name='duplicate_list'),
    
    # List Items
    path('lists/<int:list_id>/items/add/', views.AddListItemView.as_view(), name='add_list_item'),
    path('lists/<int:list_id>/items/<int:item_id>/toggle/', views.ToggleListItemView.as_view(), name='toggle_list_item'),
    path('lists/<int:list_id>/items/<int:item_id>/price/', views.UpdateListItemPriceView.as_view(), name='update_item_price'),
    path('lists/<int:list_id>/items/<int:item_id>/remove/', views.RemoveListItemView.as_view(), name='remove_list_item'),
    
    # Grocery Items
    path('items/create/', views.GroceryItemCreateView.as_view(), name='create_item'),
    path('items/<int:pk>/', views.GroceryItemDetailView.as_view(), name='item_detail'),
    path('items/<int:pk>/edit/', views.GroceryItemUpdateView.as_view(), name='edit_item'),
    
    # Barcode API Endpoint
    path('api/items/barcode/<str:barcode>/', views.BarcodeSearchView.as_view(), name='barcode_search'),
    
    # Families
    path('families/', views.FamilyListView.as_view(), name='family'),
    path('families/create/', views.FamilyCreateView.as_view(), name='create_family'),
    path('families/<int:pk>/', views.FamilyDetailView.as_view(), name='family_detail'),
    path('families/<int:pk>/edit/', views.FamilyUpdateView.as_view(), name='edit_family'),
    path('families/<int:pk>/invite/', views.InviteFamilyMemberView.as_view(), name='invite_member'),
    
    # Stores
    path('stores/', views.StoreListView.as_view(), name='stores'),
    path('stores/create/', views.StoreCreateView.as_view(), name='create_store'),
    path('stores/<int:pk>/', views.StoreDetailView.as_view(), name='store_detail'),
    path('stores/<int:pk>/edit/', views.StoreUpdateView.as_view(), name='edit_store'),
    
    # Store Locations
    path('stores/<int:store_id>/locations/add/', views.AddStoreLocationView.as_view(), name='add_location'),
    path('stores/<int:store_id>/locations/<int:pk>/edit/', views.EditStoreLocationView.as_view(), name='edit_location'),
    path('stores/<int:store_id>/locations/<int:pk>/delete/', views.DeleteStoreLocationView.as_view(), name='delete_location'),
    
    # API endpoints
    path('api/items/search/', views.GroceryItemSearchView.as_view(), name='item_search'),
    
    # User Profile
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/edit/', views.UserProfileUpdateView.as_view(), name='edit_profile'),
    path('profile/theme/', views.UpdateThemeView.as_view(), name='update_theme'),
]