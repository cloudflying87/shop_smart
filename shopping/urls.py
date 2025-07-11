from django.urls import path
from . import views
from .store_utils_view import StorePopulationView, delete_all_stores, delete_store

app_name = 'groceries'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Offline page
    path('offline/', views.OfflineView.as_view(), name='offline'),
    
    # Shopping Lists
    path('lists/', views.ShoppingListListView.as_view(), name='lists'),
    path('lists/create/', views.ShoppingListCreateView.as_view(), name='create_list'),
    path('lists/bulk-import/', views.BulkImportView.as_view(), name='bulk_import'),
    path('lists/bulk-import/confirm/', views.BulkImportConfirmView.as_view(), name='bulk_import_confirm'),
    path('lists/<int:pk>/', views.ShoppingListDetailView.as_view(), name='list_detail'),
    path('lists/<int:pk>/edit/', views.ShoppingListUpdateView.as_view(), name='edit_list'),
    path('lists/<int:pk>/delete/', views.ShoppingListDeleteView.as_view(), name='delete_list'),
    path('lists/<int:pk>/complete/', views.ShoppingListCompleteView.as_view(), name='complete_list'),
    path('lists/<int:pk>/reopen/', views.ShoppingListReopenView.as_view(), name='reopen_list'),
    path('lists/<int:pk>/duplicate/', views.ShoppingListDuplicateView.as_view(), name='duplicate_list'),
    
    # List Items
    path('lists/<int:list_id>/items/add/', views.AddListItemView.as_view(), name='add_list_item'),
    path('lists/<int:list_id>/items/categories/', views.CategoryItemSelectionView.as_view(), name='category_selection'),
    path('lists/<int:list_id>/items/add-multiple/', views.AddMultipleItemsView.as_view(), name='add_multiple_items'),
    path('lists/<int:list_id>/items/<int:item_id>/toggle/', views.ToggleListItemView.as_view(), name='toggle_list_item'),
    path('lists/<int:list_id>/items/<int:item_id>/price/', views.UpdateListItemPriceView.as_view(), name='update_item_price'),
    path('lists/<int:list_id>/items/<int:item_id>/location/', views.UpdateListItemLocationView.as_view(), name='update_item_location'),
    path('lists/<int:list_id>/items/<int:item_id>/get-location/', views.GetListItemLocationView.as_view(), name='get_item_location'),
    path('lists/<int:list_id>/items/<int:item_id>/quantity/', views.UpdateListItemQuantityView.as_view(), name='update_item_quantity'),
    path('lists/<int:list_id>/items/<int:item_id>/note/', views.UpdateListItemNoteView.as_view(), name='update_item_note'),
    path('lists/<int:list_id>/items/<int:item_id>/remove/', views.RemoveListItemView.as_view(), name='remove_list_item'),
    
    # Grocery Items
    path('items/', views.GroceryItemListView.as_view(), name='items'),
    path('items/create/', views.GroceryItemCreateView.as_view(), name='create_item'),
    path('items/<int:pk>/', views.GroceryItemDetailView.as_view(), name='item_detail'),
    path('items/<int:pk>/edit/', views.GroceryItemUpdateView.as_view(), name='edit_item'),
    path('items/<int:pk>/delete/', views.GroceryItemDeleteView.as_view(), name='delete_item'),
    path('items/<int:pk>/store-locations/', views.ItemStoreLocationView.as_view(), name='item_store_locations'),
    
    # Barcode API Endpoint - duplicated at the root level in shop_smart/urls.py
    # path('api/items/barcode/<str:barcode>/', views.BarcodeSearchView.as_view(), name='barcode_search'),
    
    # Families
    path('families/', views.FamilyListView.as_view(), name='family'),
    path('families/create/', views.FamilyCreateView.as_view(), name='create_family'),
    path('families/<int:pk>/', views.FamilyDetailView.as_view(), name='family_detail'),
    path('families/<int:pk>/edit/', views.FamilyUpdateView.as_view(), name='edit_family'),
    path('families/<int:pk>/invite/', views.InviteFamilyMemberView.as_view(), name='invite_member'),
    path('families/<int:pk>/members/<int:member_pk>/update/', views.UpdateFamilyMemberView.as_view(), name='update_member'),
    path('families/<int:pk>/members/<int:member_pk>/remove/', views.RemoveFamilyMemberView.as_view(), name='remove_member'),
    
    # Stores
    path('stores/', views.StoreListView.as_view(), name='stores'),
    path('stores/create/', views.StoreCreateView.as_view(), name='create_store'),
    path('stores/populate/', StorePopulationView.as_view(), name='populate_stores'),
    path('stores/delete-all/', delete_all_stores, name='delete_all_stores'),
    path('stores/<int:pk>/', views.StoreDetailView.as_view(), name='store_detail'),
    path('stores/<int:pk>/edit/', views.StoreUpdateView.as_view(), name='edit_store'),
    path('stores/<int:pk>/delete/', delete_store, name='delete_store'),
    
    # Store Locations
    path('stores/<int:store_id>/locations/add/', views.AddStoreLocationView.as_view(), name='add_location'),
    path('stores/<int:store_id>/locations/<int:pk>/edit/', views.EditStoreLocationView.as_view(), name='edit_location'),
    path('stores/<int:store_id>/locations/<int:pk>/delete/', views.DeleteStoreLocationView.as_view(), name='delete_location'),
    
    # API endpoints - these are duplicated at the root level in shop_smart/urls.py
    # path('api/items/search/', views.GroceryItemSearchView.as_view(), name='item_search'),
    path('api/stores/search/', views.StoreSearchView.as_view(), name='store_search'),
    
    # User Profile
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/edit/', views.UserProfileUpdateView.as_view(), name='edit_profile'),
    path('profile/theme/', views.UpdateThemeView.as_view(), name='update_theme'),
    # Category toggle path removed
]