from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

class Family(models.Model):
    """Family group for sharing shopping lists"""
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_families')
    
    class Meta:
        verbose_name_plural = 'Families'
    
    def __str__(self):
        return self.name
    
    def get_suggested_items(self, store=None, limit=20):
        """Get suggested items for this family based on purchase history"""
        # Get family's frequently purchased items
        family_items = FamilyItemUsage.objects.filter(family=self).order_by('-usage_count')
        
        if store:
            # Filter by store if specified
            store_items = ItemStoreInfo.objects.filter(store=store).values_list('item_id', flat=True)
            family_items = family_items.filter(item_id__in=store_items)
        
        # Get the item IDs ordered by usage count
        item_ids = family_items.values_list('item_id', flat=True)[:limit]
        
        # Get the actual item objects
        if item_ids:
            return GroceryItem.objects.filter(id__in=item_ids)
        
        # Fallback to global popular items if the family has no history
        if store:
            return GroceryItem.objects.filter(
                store_info__store=store
            ).order_by('-global_popularity')[:limit]
        
        return GroceryItem.objects.order_by('-global_popularity')[:limit]


class FamilyMember(models.Model):
    """Associates users with families"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='family_memberships')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='members')
    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'family')
    
    def __str__(self):
        return f"{self.user.username} ({self.family.name})"


class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    default_family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True, blank=True, related_name='default_for_users')
    dark_mode = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Profile for {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a profile when a user is created"""
    if created:
        UserProfile.objects.create(user=instance)


class GroceryStore(models.Model):
    """Store where groceries are purchased"""
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    families = models.ManyToManyField(Family, related_name='stores', blank=True)
    logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    slug = models.SlugField(unique=True, max_length=100)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class StoreLocation(models.Model):
    """Zones or areas within a store (e.g. produce, dairy, etc.)"""
    name = models.CharField(max_length=100)
    store = models.ForeignKey(GroceryStore, on_delete=models.CASCADE, related_name='locations')
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['sort_order', 'name']
        unique_together = ('name', 'store')
    
    def __str__(self):
        return f"{self.name} ({self.store.name})"


class ProductCategory(models.Model):
    """Categories for grocery items (e.g. dairy, produce, meat, etc.)"""
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    sort_order = models.IntegerField(default=0)
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Icon name for category")
    
    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Product Categories'
    
    def __str__(self):
        return self.name
    
    @property
    def full_path(self):
        """Return the full category path (e.g. Food > Dairy > Yogurt)"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


class GroceryItem(models.Model):
    """Grocery items that can be added to shopping lists"""
    # Core fields
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, related_name='items')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    global_popularity = models.IntegerField(default=0, help_text="Global popularity count across all families")
    
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
    
    class Meta:
        ordering = ['-global_popularity', 'name']
    
    def __str__(self):
        return self.name
    
    def increment_popularity(self, family=None):
        """Increment the popularity counter when item is added to a list"""
        self.global_popularity += 1
        self.save(update_fields=['global_popularity'])
        
        if family:
            # Also increment the family-specific counter
            usage, created = FamilyItemUsage.objects.get_or_create(
                family=family,
                item=self,
                defaults={'usage_count': 1}
            )
            
            if not created:
                usage.usage_count += 1
                usage.save(update_fields=['usage_count'])


class FamilyItemUsage(models.Model):
    """Tracks how often a family uses a specific item"""
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='item_usage')
    item = models.ForeignKey(GroceryItem, on_delete=models.CASCADE, related_name='family_usage')
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('family', 'item')
        ordering = ['-usage_count', '-last_used']
    
    def __str__(self):
        return f"{self.item.name} used {self.usage_count} times by {self.family.name}"


class ItemStoreInfo(models.Model):
    """Association between grocery items and stores, with additional data"""
    item = models.ForeignKey(GroceryItem, on_delete=models.CASCADE, related_name='store_info')
    store = models.ForeignKey(GroceryStore, on_delete=models.CASCADE)
    location = models.ForeignKey(StoreLocation, on_delete=models.SET_NULL, null=True, blank=True)
    typical_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    last_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    last_purchased = models.DateTimeField(null=True, blank=True)
    average_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ('item', 'store')
        verbose_name_plural = 'Item Store Info'
    
    def __str__(self):
        return f"{self.item.name} at {self.store.name}"


class ShoppingList(models.Model):
    """Shopping list for a family"""
    name = models.CharField(max_length=100)
    store = models.ForeignKey(GroceryStore, on_delete=models.CASCADE, related_name='lists')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='lists')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_lists')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.store.name} ({self.created_at.strftime('%Y-%m-%d')})"
    
    @property
    def total_items(self):
        return self.items.count()
    
    @property
    def checked_items(self):
        return self.items.filter(checked=True).count()
    
    @property
    def progress_percentage(self):
        if self.total_items == 0:
            return 0
        return int((self.checked_items / self.total_items) * 100)
    
    def duplicate(self, new_name=None):
        """Create a duplicate of this list"""
        if not new_name:
            new_name = f"Copy of {self.name}"
        
        new_list = ShoppingList.objects.create(
            name=new_name,
            store=self.store,
            family=self.family,
            created_by=self.created_by
        )
        
        # Copy all items to the new list
        for item in self.items.all():
            ShoppingListItem.objects.create(
                shopping_list=new_list,
                item=item.item,
                quantity=item.quantity,
                unit=item.unit,
                note=item.note,
                sort_order=item.sort_order
            )
        
        return new_list


class ShoppingListItem(models.Model):
    """Individual items on a shopping list"""
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(GroceryItem, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    unit = models.CharField(max_length=20, blank=True, null=True, help_text="e.g. kg, lbs, pkg")
    checked = models.BooleanField(default=False)
    actual_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['checked', 'sort_order']
    
    def __str__(self):
        return f"{self.item.name} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        # Increment item popularity for this family
        is_new = self.pk is None
        
        # Only increment on creation, not update
        if is_new and self.shopping_list.family:
            self.item.increment_popularity(family=self.shopping_list.family)
        
        super().save(*args, **kwargs)


class SyncLog(models.Model):
    """For tracking offline changes that need to be synced"""
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
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.operation} {self.model_name} #{self.record_id} by {self.user.username}"