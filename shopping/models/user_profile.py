from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    default_family = models.ForeignKey('Family', on_delete=models.SET_NULL, null=True, blank=True, related_name='default_for_users')
    dark_mode = models.BooleanField(default=False)
    show_categories = models.BooleanField(default=False)  # Always using flat list
    
    # Allergen preferences as a JSON field
    allergens = models.JSONField(default=dict, blank=True, help_text="User allergen preferences")
    
    # Dietary preferences as a JSON field
    dietary_preferences = models.JSONField(default=dict, blank=True, help_text="User dietary preferences")
    
    def __str__(self):
        return f"Profile for {self.user.username}"
    
    def get_allergens(self):
        """Get user's allergen preferences as a list"""
        if isinstance(self.allergens, list):
            return self.allergens
        return self.allergens.get('selected', [])
    
    def set_allergens(self, allergen_list):
        """Set user's allergen preferences"""
        if not isinstance(self.allergens, dict):
            self.allergens = {}
        
        self.allergens['selected'] = allergen_list
        self.save(update_fields=['allergens'])
    
    def get_preferences(self):
        """Get user's dietary preferences as a list"""
        if isinstance(self.dietary_preferences, list):
            return self.dietary_preferences
        return self.dietary_preferences.get('selected', [])
    
    def set_preferences(self, preference_list):
        """Set user's dietary preferences"""
        if not isinstance(self.dietary_preferences, dict):
            self.dietary_preferences = {}
        
        self.dietary_preferences['selected'] = preference_list
        self.save(update_fields=['dietary_preferences'])


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a profile when a user is created"""
    if created:
        UserProfile.objects.create(user=instance)