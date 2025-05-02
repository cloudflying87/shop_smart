from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Family, FamilyMember, UserProfile, GroceryStore, StoreLocation,
    ProductCategory, GroceryItem, FamilyItemUsage, ItemStoreInfo,
    ShoppingList, ShoppingListItem, SyncLog
)

@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'created_by', 'member_count')
    search_fields = ('name',)
    list_filter = ('created_at',)
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'family', 'is_admin', 'joined_at')
    list_filter = ('is_admin', 'joined_at', 'family')
    search_fields = ('user__username', 'family__name')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'default_family', 'dark_mode')
    list_filter = ('dark_mode',)
    search_fields = ('user__username', 'default_family__name')


@admin.register(GroceryStore)
class GroceryStoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'location_count', 'display_logo')
    search_fields = ('name', 'address')
    prepopulated_fields = {'slug': ('name',)}
    
    def location_count(self, obj):
        return obj.locations.count()
    location_count.short_description = 'Locations'
    
    def display_logo(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="auto" />', obj.logo.url)
        return "No logo"
    display_logo.short_description = 'Logo'


@admin.register(StoreLocation)
class StoreLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'sort_order')
    list_filter = ('store',)
    search_fields = ('name', 'store__name')
    list_editable = ('sort_order',)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'sort_order', 'icon')
    list_filter = ('parent',)
    search_fields = ('name',)
    list_editable = ('sort_order', 'icon')


@admin.register(GroceryItem)
class GroceryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'barcode', 'created_by', 'global_popularity')
    list_filter = ('category', 'is_verified', 'is_user_added', 'created_at')
    search_fields = ('name', 'barcode', 'brand', 'description')
    readonly_fields = ('global_popularity', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'created_by')
        }),
        ('Product Details', {
            'fields': ('barcode', 'brand', 'image_url', 'off_id')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_user_added', 'global_popularity', 'created_at', 'updated_at')
        }),
    )


@admin.register(ItemStoreInfo)
class ItemStoreInfoAdmin(admin.ModelAdmin):
    list_display = ('item', 'store', 'location', 'typical_price', 'last_price', 'last_purchased')
    list_filter = ('store', 'location', 'last_purchased')
    search_fields = ('item__name', 'store__name')
    readonly_fields = ('last_purchased',)


@admin.register(FamilyItemUsage)
class FamilyItemUsageAdmin(admin.ModelAdmin):
    list_display = ('item', 'family', 'usage_count', 'last_used')
    list_filter = ('family', 'last_used')
    search_fields = ('item__name', 'family__name')
    readonly_fields = ('last_used',)


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'family', 'created_by', 'created_at', 'completed', 'item_count')
    list_filter = ('store', 'family', 'completed', 'created_at')
    search_fields = ('name', 'store__name', 'family__name', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'


@admin.register(ShoppingListItem)
class ShoppingListItemAdmin(admin.ModelAdmin):
    list_display = ('item', 'shopping_list', 'quantity', 'unit', 'checked', 'actual_price')
    list_filter = ('checked', 'shopping_list__family', 'shopping_list__store')
    search_fields = ('item__name', 'shopping_list__name')
    list_editable = ('checked', 'quantity', 'unit', 'actual_price')


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('operation', 'model_name', 'record_id', 'user', 'timestamp', 'synced')
    list_filter = ('operation', 'model_name', 'synced', 'timestamp')
    search_fields = ('user__username', 'model_name', 'record_id')
    readonly_fields = ('timestamp', 'synced_at')
