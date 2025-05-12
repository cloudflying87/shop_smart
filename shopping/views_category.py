from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.db.models import Count
from django.contrib import messages

from .models import (
    ShoppingList, ShoppingListItem, GroceryItem, ProductCategory, FamilyMember
)

class CategoryItemSelectionView(LoginRequiredMixin, View):
    """View for selecting items by category to add to a shopping list"""
    template_name = 'groceries/lists/category_selection.html'
    
    def get(self, request, list_id):
        # Get shopping list
        shopping_list = get_object_or_404(ShoppingList, pk=list_id)
        
        # Check user permissions
        if not FamilyMember.objects.filter(user=request.user, family=shopping_list.family).exists():
            return HttpResponseForbidden("You don't have permission to view this list")
        
        # Get all categories with items
        categories = ProductCategory.objects.annotate(
            item_count=Count('items')
        ).filter(item_count__gt=0).order_by('name')
        
        # Get items for each category
        items_by_category = {}
        for category in categories:
            items_by_category[category.id] = GroceryItem.objects.filter(
                category=category
            ).order_by('name')
        
        context = {
            'list': shopping_list,
            'categories': categories,
            'items_by_category': items_by_category,
        }
        
        return render(request, self.template_name, context)

class AddMultipleItemsView(LoginRequiredMixin, View):
    """View for adding multiple items to a shopping list"""
    
    def post(self, request, list_id):
        # Get shopping list
        shopping_list = get_object_or_404(ShoppingList, pk=list_id)
        
        # Check user permissions
        if not FamilyMember.objects.filter(user=request.user, family=shopping_list.family).exists():
            return HttpResponseForbidden("You don't have permission to edit this list")
        
        # Get item IDs from form data
        item_ids = request.POST.getlist('item_ids')
        default_quantity = request.POST.get('default_quantity', 1)
        default_unit = request.POST.get('default_unit', '')
        
        # Add each item to the shopping list
        added_count = 0
        for item_id in item_ids:
            try:
                # Get the grocery item
                grocery_item = GroceryItem.objects.get(pk=item_id)
                
                # Check if item already exists in the shopping list
                existing_item = ShoppingListItem.objects.filter(
                    shopping_list=shopping_list,
                    item=grocery_item
                ).first()
                
                if existing_item:
                    # Update existing item quantity
                    existing_item.quantity += float(default_quantity)
                    existing_item.save()
                else:
                    # Create new shopping list item
                    ShoppingListItem.objects.create(
                        shopping_list=shopping_list,
                        item=grocery_item,
                        quantity=default_quantity,
                        unit=default_unit
                    )
                
                added_count += 1
            except GroceryItem.DoesNotExist:
                continue
        
        messages.success(request, f"Added {added_count} items to your shopping list")
        return redirect('groceries:list_detail', pk=list_id)