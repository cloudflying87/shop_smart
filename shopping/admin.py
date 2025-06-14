from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum, Avg, Q
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
import csv
from datetime import datetime, timedelta

from .models import (
    Family, FamilyMember, UserProfile, GroceryStore, StoreLocation,
    ProductCategory, GroceryItem, FamilyItemUsage, ItemStoreInfo,
    ShoppingList, ShoppingListItem, SyncLog
)

# Custom admin site
class ShopSmartAdminSite(admin.AdminSite):
    site_header = "ShopSmart Administration"
    site_title = "ShopSmart Admin"
    index_title = "Welcome to ShopSmart Admin Panel"
    
    def get_urls(self):
        urls = super().get_urls()
        from django.urls import path
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='admin_dashboard'),
            path('reports/', self.admin_view(self.reports_view), name='admin_reports'),
            path('export-data/', self.admin_view(self.export_data_view), name='admin_export_data'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        # Get statistics
        context = {
            'title': 'Dashboard',
            'total_users': UserProfile.objects.count(),
            'total_families': Family.objects.count(),
            'total_stores': GroceryStore.objects.count(),
            'total_items': GroceryItem.objects.count(),
            'total_lists': ShoppingList.objects.count(),
            'active_lists': ShoppingList.objects.filter(completed=False).count(),
            'recent_lists': ShoppingList.objects.order_by('-created_at')[:5],
            'popular_items': GroceryItem.objects.order_by('-global_popularity')[:10],
            'active_families': Family.objects.annotate(
                list_count=Count('shopping_lists')
            ).order_by('-list_count')[:5]
        }
        return TemplateResponse(request, 'admin/dashboard.html', context)
    
    def reports_view(self, request):
        # Generate various reports
        context = {
            'title': 'Reports',
        }
        return TemplateResponse(request, 'admin/reports.html', context)
    
    def export_data_view(self, request):
        # Export data functionality
        export_type = request.GET.get('type', 'users')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="shopsmart_{export_type}_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        
        if export_type == 'users':
            writer.writerow(['Username', 'Email', 'Date Joined', 'Last Login', 'Family', 'Lists Created'])
            users = UserProfile.objects.select_related('user', 'default_family')
            for profile in users:
                writer.writerow([
                    profile.user.username,
                    profile.user.email,
                    profile.user.date_joined,
                    profile.user.last_login,
                    profile.default_family.name if profile.default_family else '',
                    profile.user.created_lists.count()
                ])
        
        return response

# Register the custom admin site
admin_site = ShopSmartAdminSite(name='shopmartadmin')

# Enhanced Admin Classes
@admin.register(Family, site=admin_site)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_members', 'total_lists', 'active_lists', 'created_at', 'created_by')
    search_fields = ('name', 'created_by__username')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'created_by')
    inlines = []
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            member_count=Count('members'),
            list_count=Count('shopping_lists'),
            active_list_count=Count('shopping_lists', filter=Q(shopping_lists__completed=False))
        )
    
    def display_members(self, obj):
        members = obj.members.all()[:3]
        member_list = ', '.join([m.user.username for m in members])
        if obj.members.count() > 3:
            member_list += f' ... (+{obj.members.count() - 3} more)'
        return member_list
    display_members.short_description = 'Members'
    
    def total_lists(self, obj):
        return obj.list_count
    total_lists.admin_order_field = 'list_count'
    total_lists.short_description = 'Total Lists'
    
    def active_lists(self, obj):
        return obj.active_list_count
    active_lists.admin_order_field = 'active_list_count'
    active_lists.short_description = 'Active Lists'
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<int:family_id>/stats/', 
                self.admin_site.admin_view(self.family_stats_view), 
                name='family_stats'),
        ]
        return my_urls + urls
    
    @method_decorator(staff_member_required)
    def family_stats_view(self, request, family_id):
        family = Family.objects.get(pk=family_id)
        context = dict(
            self.admin_site.each_context(request),
            family=family,
            title=f'Statistics for {family.name}',
        )
        return TemplateResponse(request, 'admin/family_stats.html', context)


@admin.register(FamilyMember, site=admin_site)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'family', 'is_admin', 'joined_at', 'lists_created', 'items_added')
    list_filter = ('is_admin', 'joined_at', 'family')
    search_fields = ('user__username', 'user__email', 'family__name')
    readonly_fields = ('joined_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            lists_created=Count('user__created_lists'),
            items_added=Count('user__created_items')
        )
    
    def lists_created(self, obj):
        return obj.lists_created
    lists_created.admin_order_field = 'lists_created'
    
    def items_added(self, obj):
        return obj.items_added
    items_added.admin_order_field = 'items_added'


@admin.register(UserProfile, site=admin_site)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'default_family', 'dark_mode', 'lists_count', 'items_count', 'last_active')
    list_filter = ('dark_mode',)
    search_fields = ('user__username', 'user__email', 'default_family__name')
    readonly_fields = ()
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'default_family')
        }),
        ('Preferences', {
            'fields': ('dark_mode', 'show_categories')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'default_family')
    
    def lists_count(self, obj):
        return obj.user.created_lists.count()
    lists_count.short_description = 'Lists Created'
    
    def items_count(self, obj):
        return obj.user.groceryitem_set.count()
    items_count.short_description = 'Items Added'
    
    def last_active(self, obj):
        return obj.user.last_login
    last_active.short_description = 'Last Active'


@admin.register(GroceryStore, site=admin_site)
class GroceryStoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_logo', 'location_count', 'total_products', 'total_lists')
    list_filter = ()
    search_fields = ('name', 'address')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('display_logo_large',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'address', 'website')
        }),
        ('Media', {
            'fields': ('logo', 'display_logo_large'),
            'classes': ('collapse',)
        }),
        ('Family Association', {
            'fields': ('families',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            location_count=Count('locations'),
            product_count=Count('item_info'),
            list_count=Count('shopping_lists')
        )
    
    def location_count(self, obj):
        return obj.location_count
    location_count.admin_order_field = 'location_count'
    location_count.short_description = '# Locations'
    
    def total_products(self, obj):
        return obj.product_count
    total_products.admin_order_field = 'product_count'
    total_products.short_description = '# Products'
    
    def total_lists(self, obj):
        return obj.list_count
    total_lists.admin_order_field = 'list_count'
    total_lists.short_description = '# Lists'
    
    def display_logo(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: contain;" />', obj.logo.url)
        return "No logo"
    display_logo.short_description = 'Logo'
    
    def display_logo_large(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="200" height="200" style="object-fit: contain;" />', obj.logo.url)
        return "No logo"
    display_logo_large.short_description = 'Logo Preview'
    
    # Remove actions that reference non-existent fields


class StoreLocationInline(admin.TabularInline):
    model = StoreLocation
    extra = 1
    fields = ('name', 'sort_order')


@admin.register(StoreLocation, site=admin_site)
class StoreLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'sort_order', 'items_count')
    list_filter = ('store',)
    search_fields = ('name', 'store__name')
    list_editable = ('sort_order',)
    ordering = ('store', 'sort_order')
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            items_count=Count('item_store_infos')
        )
    
    def items_count(self, obj):
        return obj.items_count
    items_count.admin_order_field = 'items_count'
    items_count.short_description = '# Items'


@admin.register(ProductCategory, site=admin_site)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'icon', 'sort_order', 'items_count', 'subcategory_count')
    list_filter = ('parent',)
    search_fields = ('name',)
    list_editable = ('sort_order', 'icon')
    ordering = ('parent', 'sort_order', 'name')
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            items_count=Count('items'),
            subcategory_count=Count('children')
        )
    
    def items_count(self, obj):
        return obj.items_count
    items_count.admin_order_field = 'items_count'
    items_count.short_description = '# Items'
    
    def subcategory_count(self, obj):
        return obj.subcategory_count
    subcategory_count.admin_order_field = 'subcategory_count'
    subcategory_count.short_description = '# Subcategories'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'parent':
            kwargs['queryset'] = ProductCategory.objects.filter(parent__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(GroceryItem, site=admin_site)
class GroceryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'barcode', 'display_image', 'times_used', 'avg_price', 'popularity_score')
    list_filter = ('category', 'is_verified', 'is_user_added', 'created_at')
    search_fields = ('name', 'barcode', 'brand', 'description')
    readonly_fields = ('global_popularity', 'created_at', 'updated_at', 'display_image_large')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'created_by')
        }),
        ('Product Details', {
            'fields': ('barcode', 'brand', 'off_id')
        }),
        ('Media', {
            'fields': ('image_url', 'display_image_large'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('is_verified', 'is_user_added', 'global_popularity'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            times_used=Count('list_items'),
            avg_price=Avg('store_info__last_price')
        ).select_related('category', 'created_by')
    
    def times_used(self, obj):
        return obj.times_used
    times_used.admin_order_field = 'times_used'
    times_used.short_description = 'Times Used'
    
    def avg_price(self, obj):
        if obj.avg_price:
            return f'${obj.avg_price:.2f}'
        return '-'
    avg_price.admin_order_field = 'avg_price'
    avg_price.short_description = 'Avg Price'
    
    def popularity_score(self, obj):
        return f'{obj.global_popularity:.1f}'
    popularity_score.admin_order_field = 'global_popularity'
    popularity_score.short_description = 'Popularity'
    
    def display_image(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: contain;" />', obj.image_url)
        return "No image"
    display_image.short_description = 'Image'
    
    def display_image_large(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" width="200" height="200" style="object-fit: contain;" />', obj.image_url)
        return "No image"
    display_image_large.short_description = 'Image Preview'
    
    actions = ['verify_items', 'unverify_items']
    
    def verify_items(self, request, queryset):
        updated = queryset.update(is_verified=True)
        messages.success(request, f'{updated} items verified.')
    verify_items.short_description = 'Verify selected items'
    
    def unverify_items(self, request, queryset):
        updated = queryset.update(is_verified=False)
        messages.success(request, f'{updated} items unverified.')
    unverify_items.short_description = 'Unverify selected items'


@admin.register(ItemStoreInfo, site=admin_site)
class ItemStoreInfoAdmin(admin.ModelAdmin):
    list_display = ('item', 'store', 'location', 'typical_price', 'last_price', 'price_difference', 'last_purchased')
    list_filter = ('store', 'location', 'last_purchased')
    search_fields = ('item__name', 'store__name')
    readonly_fields = ('last_purchased',)
    list_editable = ('typical_price', 'last_price')
    
    def price_difference(self, obj):
        if obj.typical_price and obj.last_price:
            diff = obj.last_price - obj.typical_price
            color = 'green' if diff < 0 else 'red' if diff > 0 else 'black'
            return format_html(
                '<span style="color: {};">{}</span>',
                color,
                f'${diff:+.2f}'
            )
        return '-'
    price_difference.short_description = 'Price Diff'


@admin.register(FamilyItemUsage, site=admin_site)
class FamilyItemUsageAdmin(admin.ModelAdmin):
    list_display = ('item', 'family', 'usage_count', 'last_used', 'avg_quantity', 'frequency')
    list_filter = ('family', 'last_used')
    search_fields = ('item__name', 'family__name')
    readonly_fields = ('last_used',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('item', 'family')
    
    def avg_quantity(self, obj):
        # Calculate average quantity from shopping list items
        avg = obj.family.shopping_lists.filter(
            items__item=obj.item
        ).aggregate(avg=Avg('items__quantity'))['avg']
        return f'{avg:.1f}' if avg else '-'
    avg_quantity.short_description = 'Avg Qty'
    
    def frequency(self, obj):
        # Calculate purchase frequency
        if obj.usage_count > 1:
            first_use = obj.family.shopping_lists.filter(
                items__item=obj.item
            ).order_by('created_at').first()
            if first_use:
                days = (obj.last_used - first_use.created_at).days
                if days > 0:
                    return f'Every {days/obj.usage_count:.0f} days'
        return '-'
    frequency.short_description = 'Frequency'


class ShoppingListItemInline(admin.TabularInline):
    model = ShoppingListItem
    extra = 0
    fields = ('item', 'quantity', 'unit', 'checked', 'actual_price')
    raw_id_fields = ('item',)


@admin.register(ShoppingList, site=admin_site)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'family', 'created_by', 'status_badge', 'item_count', 'progress', 'total_cost', 'created_at')
    list_filter = ('completed', 'store', 'family', 'created_at')
    search_fields = ('name', 'store__name', 'family__name', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    inlines = [ShoppingListItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'store', 'family', 'created_by')
        }),
        ('Status', {
            'fields': ('completed', 'completed_at'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            item_count=Count('items'),
            checked_count=Count('items', filter=Q(items__checked=True)),
            total_cost=Sum('items__actual_price')
        ).select_related('store', 'family', 'created_by')
    
    def status_badge(self, obj):
        if obj.completed:
            return format_html('<span style="color: green;">✓ Completed</span>')
        return format_html('<span style="color: orange;">⏳ Active</span>')
    status_badge.short_description = 'Status'
    
    def item_count(self, obj):
        return obj.item_count
    item_count.admin_order_field = 'item_count'
    item_count.short_description = '# Items'
    
    def progress(self, obj):
        if obj.item_count > 0:
            percentage = (obj.checked_count / obj.item_count) * 100
            color = 'green' if percentage == 100 else 'orange' if percentage > 50 else 'red'
            return format_html(
                '<div style="width: 100px; background-color: #f0f0f0; border-radius: 4px;">'
                '<div style="width: {}%; background-color: {}; color: white; text-align: center; border-radius: 4px;">'
                '{:.0f}%</div></div>',
                percentage, color, percentage
            )
        return '-'
    progress.short_description = 'Progress'
    
    def total_cost(self, obj):
        if obj.total_cost:
            return f'${obj.total_cost:.2f}'
        return '-'
    total_cost.admin_order_field = 'total_cost'
    total_cost.short_description = 'Total Cost'
    
    actions = ['mark_completed', 'mark_active', 'duplicate_list']
    
    def mark_completed(self, request, queryset):
        updated = queryset.update(completed=True, completed_at=datetime.now())
        messages.success(request, f'{updated} lists marked as completed.')
    mark_completed.short_description = 'Mark selected lists as completed'
    
    def mark_active(self, request, queryset):
        updated = queryset.update(completed=False, completed_at=None)
        messages.success(request, f'{updated} lists marked as active.')
    mark_active.short_description = 'Mark selected lists as active'
    
    def duplicate_list(self, request, queryset):
        for list_obj in queryset:
            new_list = ShoppingList.objects.create(
                name=f'{list_obj.name} (Copy)',
                store=list_obj.store,
                family=list_obj.family,
                created_by=request.user
            )
            for item in list_obj.items.all():
                ShoppingListItem.objects.create(
                    shopping_list=new_list,
                    item=item.item,
                    quantity=item.quantity,
                    unit=item.unit,
                    note=item.note
                )
        messages.success(request, f'{queryset.count()} lists duplicated.')
    duplicate_list.short_description = 'Duplicate selected lists'


@admin.register(ShoppingListItem, site=admin_site)
class ShoppingListItemAdmin(admin.ModelAdmin):
    list_display = ('item', 'shopping_list', 'quantity', 'unit', 'checked', 'actual_price', 'price_status')
    list_filter = ('checked', 'shopping_list__family', 'shopping_list__store')
    search_fields = ('item__name', 'shopping_list__name', 'note')
    list_editable = ('checked', 'quantity', 'unit', 'actual_price')
    raw_id_fields = ('item', 'shopping_list')
    
    def price_status(self, obj):
        if obj.actual_price:
            # Compare with typical price
            store_info = ItemStoreInfo.objects.filter(
                item=obj.item,
                store=obj.shopping_list.store
            ).first()
            if store_info and store_info.typical_price:
                diff_percent = ((obj.actual_price - store_info.typical_price) / store_info.typical_price) * 100
                if diff_percent > 10:
                    return format_html('<span style="color: red;">↑ {:.0f}%</span>', diff_percent)
                elif diff_percent < -10:
                    return format_html('<span style="color: green;">↓ {:.0f}%</span>', abs(diff_percent))
                else:
                    return format_html('<span style="color: gray;">→ Normal</span>')
        return '-'
    price_status.short_description = 'Price Status'


@admin.register(SyncLog, site=admin_site)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('operation', 'model_name', 'record_id', 'user', 'timestamp', 'sync_status')
    list_filter = ('operation', 'model_name', 'synced', 'timestamp')
    search_fields = ('user__username', 'model_name', 'record_id')
    readonly_fields = ('timestamp', 'synced_at', 'data_preview')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Operation Details', {
            'fields': ('operation', 'model_name', 'record_id', 'user')
        }),
        ('Sync Status', {
            'fields': ('synced', 'synced_at')
        }),
        ('Data', {
            'fields': ('data_preview',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )
    
    def sync_status(self, obj):
        if obj.synced:
            return format_html('<span style="color: green;">✓ Synced</span>')
        return format_html('<span style="color: orange;">⏳ Pending</span>')
    sync_status.short_description = 'Status'
    
    def data_preview(self, obj):
        return format_html('<pre>{}</pre>', obj.data[:500] + '...' if len(obj.data) > 500 else obj.data)
    data_preview.short_description = 'Data Preview'
    
    actions = ['mark_synced', 'mark_unsynced']
    
    def mark_synced(self, request, queryset):
        updated = queryset.update(synced=True, synced_at=datetime.now())
        messages.success(request, f'{updated} logs marked as synced.')
    mark_synced.short_description = 'Mark selected as synced'
    
    def mark_unsynced(self, request, queryset):
        updated = queryset.update(synced=False, synced_at=None)
        messages.success(request, f'{updated} logs marked as unsynced.')
    mark_unsynced.short_description = 'Mark selected as unsynced'


# Register all models with the custom admin site
admin.site = admin_site