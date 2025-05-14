from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import F, Count, Q, Subquery, OuterRef
from django.db import IntegrityError
from django.utils.text import slugify
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
)
from django.views.generic.base import TemplateView
from django.utils import timezone

from .models import (
    Family, FamilyMember, UserProfile, GroceryStore, GroceryItem,
    ShoppingList, ShoppingListItem, StoreLocation,
    FamilyItemUsage, ProductCategory, ItemStoreInfo
)
from .forms import (
    ShoppingListForm, FamilyForm, GroceryStoreForm, GroceryItemForm,
    StoreLocationForm, ShoppingListItemForm, UserProfileForm, FamilyMemberForm,
    UserRegistrationForm
)
from .recommender import ShoppingRecommender
from .store_utils import (
    create_default_store_locations, get_common_store_data,
    search_store_info, save_store_logo_from_url
)

# Import our local view modules
# These imports must be at the bottom to avoid circular imports

# Import category-based item selection views
from .views_category import CategoryItemSelectionView, AddMultipleItemsView

# Store Location Views
class AddStoreLocationView(LoginRequiredMixin, CreateView):
    model = StoreLocation
    form_class = StoreLocationForm
    template_name = 'groceries/stores/add_location.html'
    
    def get_success_url(self):
        return reverse('groceries:store_detail', kwargs={'pk': self.kwargs['store_id']})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        store = get_object_or_404(GroceryStore, pk=self.kwargs['store_id'])
        kwargs['store'] = store
        return kwargs
    
    def form_valid(self, form):
        store = get_object_or_404(GroceryStore, pk=self.kwargs['store_id'])
        form.instance.store = store
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = get_object_or_404(GroceryStore, pk=self.kwargs['store_id'])
        return context

class EditStoreLocationView(LoginRequiredMixin, UpdateView):
    model = StoreLocation
    form_class = StoreLocationForm
    template_name = 'groceries/stores/edit_location.html'
    
    def get_success_url(self):
        return reverse('groceries:store_detail', kwargs={'pk': self.kwargs['store_id']})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        store = get_object_or_404(GroceryStore, pk=self.kwargs['store_id'])
        kwargs['store'] = store
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = get_object_or_404(GroceryStore, pk=self.kwargs['store_id'])
        return context

class DeleteStoreLocationView(LoginRequiredMixin, DeleteView):
    model = StoreLocation
    template_name = 'groceries/stores/delete_location.html'
    
    def get_success_url(self):
        return reverse('groceries:store_detail', kwargs={'pk': self.kwargs['store_id']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['store'] = get_object_or_404(GroceryStore, pk=self.kwargs['store_id'])
        return context

# Dashboard View
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'groceries/dashboard_simple.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            user_profile = self.request.user.profile
            family = user_profile.default_family
            
            if not family and self.request.user.family_memberships.exists():
                family = self.request.user.family_memberships.first().family
            
            # Get recent lists for this family
            if family:
                context['recent_lists'] = ShoppingList.objects.filter(
                    family=family
                ).order_by('-created_at')[:5]
                
                # Get recommended items for this family
                context['recommended_items'] = ShoppingRecommender.get_recommendations_for_family(
                    family, limit=8
                )
            else:
                context['recent_lists'] = []
                context['recommended_items'] = []
            
            # Count dashboard statistics
            # Get families the user belongs to
            user_families = Family.objects.filter(members__user=self.request.user)
            context['family_count'] = user_families.count()
            
            # Get all shopping lists for these families
            context['shopping_lists_count'] = ShoppingList.objects.filter(
                family__in=user_families
            ).count()
            
            # Get all stores for these families
            context['store_count'] = GroceryStore.objects.filter(
                families__in=user_families
            ).distinct().count()
            
            # Get all products (grocery items) associated with these families
            context['product_count'] = GroceryItem.objects.filter(
                families__in=user_families
            ).distinct().count()
                
            # Get stores that user has access to through family memberships
            context['stores'] = GroceryStore.objects.filter(
                families__members__user=self.request.user
            ).distinct()
            
            context['family'] = family
            
        except Exception as e:
            messages.error(self.request, f"Error loading dashboard: {str(e)}")
            context['error'] = str(e)
            
        return context

# Shopping List Views
class ShoppingListListView(LoginRequiredMixin, ListView):
    model = ShoppingList
    template_name = 'groceries/lists/list.html'
    context_object_name = 'all_lists'
    
    def get_queryset(self):
        # Get all families the user is a member of
        families = Family.objects.filter(members__user=self.request.user)
        
        # Get all lists for these families
        return ShoppingList.objects.filter(
            family__in=families
        ).select_related('store', 'family').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Split lists by completion status
        context['active_lists'] = context['all_lists'].filter(completed=False)
        context['completed_lists'] = context['all_lists'].filter(completed=True)
        
        # Add families for filtering
        context['families'] = Family.objects.filter(members__user=self.request.user)
        
        return context

class ShoppingListCreateView(LoginRequiredMixin, CreateView):
    model = ShoppingList
    form_class = ShoppingListForm
    template_name = 'groceries/lists/create.html'
    
    def get_initial(self):
        initial = super().get_initial()
        
        # Get store from query parameter if provided
        store_id = self.request.GET.get('store')
        if store_id:
            try:
                store = GroceryStore.objects.get(
                    id=store_id, 
                    families__members__user=self.request.user
                )
                initial['store'] = store.id
            except GroceryStore.DoesNotExist:
                pass
                
        # Get or set default family
        try:
            user_profile = self.request.user.profile
            if user_profile.default_family:
                initial['family'] = user_profile.default_family.id
        except (AttributeError, UserProfile.DoesNotExist):
            # If no default family, try to get first family the user belongs to
            try:
                first_family = Family.objects.filter(
                    members__user=self.request.user
                ).first()
                if first_family:
                    initial['family'] = first_family.id
            except Exception:
                pass
                
        return initial
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
        
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        
        # Ensure user has access to the selected family
        if not FamilyMember.objects.filter(user=self.request.user, family=form.instance.family).exists():
            return HttpResponseForbidden("You don't have permission to create lists for this family")
        
        # Process template list if selected
        template_list = form.cleaned_data.get('template_list')
        
        response = super().form_valid(form)
        
        if template_list:
            # Use the template list object directly instead of trying to get its ID
            self.duplicate_template_items(template_list)
        
        messages.success(self.request, f'Shopping list "{form.instance.name}" created successfully')
        return response
    
    def get_success_url(self):
        return reverse('groceries:list_detail', kwargs={'pk': self.object.pk})
    
    def duplicate_template_items(self, template_list):
        """Duplicate items from a template list to the current list"""
        # Check if template list belongs to the same family
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
        
        # Add the store and family name to the context for custom display
        store_id = self.request.GET.get('store')
        if store_id:
            try:
                store = GroceryStore.objects.get(id=store_id)
                context['selected_store'] = store
                
                # Pre-populate list name with store name in context
                from datetime import datetime
                today = datetime.now().strftime("%A, %b %d")
                context['initial_list_name'] = f"{store.name} List - {today}"
            except GroceryStore.DoesNotExist:
                pass
        
        return context

class ShoppingListDetailView(LoginRequiredMixin, DetailView):
    model = ShoppingList
    template_name = 'groceries/lists/detail.html'
    context_object_name = 'list'
    
    def get_queryset(self):
        # Ensure user can only view lists from their families
        return ShoppingList.objects.filter(
            family__members__user=self.request.user
        ).select_related('store', 'family')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shopping_list = self.object

        # Import here to avoid circular imports
        from django.db.models import Prefetch, OuterRef, Subquery
        
        # Get list items organized with store location ordering
        list_items = shopping_list.items.select_related(
            'item', 'item__category'
        ).annotate(
            # Get location sort order only for the current store
            location_sort=Subquery(
                ItemStoreInfo.objects.filter(
                    item=OuterRef('item_id'),
                    store=shopping_list.store
                ).values('location__sort_order')[:1]
            )
        ).order_by(
            'checked',
            'location_sort',
            'sort_order',
            'item__name'
        ).distinct()
        
        # Add the current store's location information to each item
        for item in list_items:
            # Find the store_info for this item and store
            store_info = ItemStoreInfo.objects.filter(
                item=item.item,
                store=shopping_list.store
            ).select_related('location').first()
            
            # Attach it directly to the item for easy access in the template
            item.current_store_info = store_info

        # Use flat list view only
        all_items = list(list_items)    
        # Get recommendations for this list
        try:
            recommended_items = ShoppingRecommender.get_recommendations_based_on_list(
                shopping_list, limit=8
            )
        except Exception as e:
            # Use a default empty list if an error occurs
            recommended_items = []
            # The logger variable might not be defined - handle safely
            try:
                logger.error(f"Error getting recommendations: {str(e)}")
            except NameError:
                print(f"Error getting recommendations: {str(e)}")

        # Add all items to context for flat list view
        context['all_items'] = all_items
        context['recommended_items'] = recommended_items
        context['total_items'] = list_items.count()
        context['checked_items'] = list_items.filter(checked=True).count()
        context['list_items'] = list_items  # Original queryset for reference
        context['store_locations'] = StoreLocation.objects.filter(store=shopping_list.store).order_by('sort_order')
        return context

class ShoppingListUpdateView(LoginRequiredMixin, UpdateView):
    model = ShoppingList
    form_class = ShoppingListForm
    template_name = 'groceries/lists/edit.html'
    context_object_name = 'list'
    
    def get_queryset(self):
        # Ensure user can only edit lists from their families
        return ShoppingList.objects.filter(
            family__members__user=self.request.user
        )
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Shopping list "{form.instance.name}" updated successfully')
        return response
    
    def get_success_url(self):
        return reverse('groceries:list_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['families'] = Family.objects.filter(
            members__user=self.request.user
        ).distinct()
        
        context['stores'] = GroceryStore.objects.filter(
            families__in=context['families']
        ).distinct()
        
        return context

class ShoppingListDeleteView(LoginRequiredMixin, DeleteView):
    model = ShoppingList
    template_name = 'groceries/lists/confirm_delete.html'
    context_object_name = 'list'
    success_url = reverse_lazy('groceries:lists')
    
    def get_queryset(self):
        # Ensure user can only delete lists from their families
        return ShoppingList.objects.filter(
            family__members__user=self.request.user
        )
    
    def delete(self, request, *args, **kwargs):
        list_name = self.get_object().name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Shopping list "{list_name}" deleted successfully')
        return response

class ShoppingListCompleteView(LoginRequiredMixin, View):
    """Mark a shopping list as complete"""
    
    def post(self, request, pk):
        shopping_list = get_object_or_404(
            ShoppingList.objects.filter(family__members__user=request.user),
            pk=pk
        )
        
        # Update list status
        shopping_list.completed = True
        shopping_list.completed_at = timezone.now()
        shopping_list.save()
        
        messages.success(request, f'Shopping list "{shopping_list.name}" marked as complete')
        
        # Redirect based on source (detail page or lists page)
        referer = request.META.get('HTTP_REFERER', '')
        if 'lists' in referer and 'detail' not in referer:
            return redirect('groceries:lists')
        else:
            return redirect('groceries:list_detail', pk=shopping_list.id)

class ShoppingListReopenView(LoginRequiredMixin, View):
    """Reopen a completed shopping list"""
    
    def post(self, request, pk):
        shopping_list = get_object_or_404(
            ShoppingList.objects.filter(family__members__user=request.user),
            pk=pk
        )
        
        # Update list status
        shopping_list.completed = False
        shopping_list.completed_at = None
        shopping_list.save()
        
        messages.success(request, f'Shopping list "{shopping_list.name}" reopened')
        
        # Redirect based on source (detail page or lists page)
        referer = request.META.get('HTTP_REFERER', '')
        if 'lists' in referer and 'detail' not in referer:
            return redirect('groceries:lists')
        else:
            return redirect('groceries:list_detail', pk=shopping_list.id)

class ShoppingListDuplicateView(LoginRequiredMixin, View):
    """Create a duplicate of an existing shopping list"""
    
    def post(self, request, pk):
        original_list = get_object_or_404(
            ShoppingList.objects.filter(family__members__user=request.user),
            pk=pk
        )
        
        # Create duplicate list
        new_name = f"Copy of {original_list.name}"
        new_list = original_list.duplicate(new_name=new_name)
        
        messages.success(request, f'Shopping list duplicated as "{new_list.name}"')
        return redirect('groceries:list_detail', pk=new_list.id)

# List Item Views
class AddListItemView(LoginRequiredMixin, View):
    """Add an item to a shopping list"""
    
    def post(self, request, list_id):
        shopping_list = get_object_or_404(
            ShoppingList.objects.filter(family__members__user=request.user),
            pk=list_id
        )
        
        item_id = request.POST.get('item_id')
        if not item_id:
            return JsonResponse({'error': 'Item ID is required'}, status=400)
        
        try:
            item = GroceryItem.objects.get(id=item_id)
            
            # Ensure the item has a category if one isn't already assigned
            if not item.category and shopping_list.store:
                # Try to get item store info for this store
                store_info = item.store_info.filter(store=shopping_list.store).first()
                if store_info and store_info.location:
                    # Try to find a product category similar to the store location name
                    from django.db.models import Q
                    from .models import ProductCategory
                    
                    location_name = store_info.location.name.lower()
                    categories = ProductCategory.objects.filter(
                        Q(name__icontains=location_name) | 
                        Q(parent__name__icontains=location_name)
                    ).first()
                    
                    if categories:
                        item.category = categories
                        item.save(update_fields=['category'])
            
            # Create list item
            list_item = ShoppingListItem.objects.create(
                shopping_list=shopping_list,
                item=item,
                quantity=request.POST.get('quantity', 1),
                unit=request.POST.get('unit', ''),
                note=request.POST.get('note', '')
            )
            
            # Return success response
            return JsonResponse({
                'success': True,
                'item': {
                    'id': list_item.id,
                    'name': item.name,
                    'brand': item.brand,
                    'quantity': list_item.quantity,
                    'unit': list_item.unit,
                    'note': list_item.note
                }
            })
            
        except GroceryItem.DoesNotExist:
            return JsonResponse({'error': 'Item not found'}, status=404)

class ToggleListItemView(LoginRequiredMixin, View):
    """Toggle a list item's checked status"""
    
    def post(self, request, list_id, item_id):
        # Get the list item and verify permissions
        list_item = get_object_or_404(
            ShoppingListItem.objects.filter(
                shopping_list__family__members__user=request.user,
                shopping_list_id=list_id
            ),
            pk=item_id
        )
        
        # Toggle checked status
        list_item.checked = not list_item.checked
        
        # Update sort_order based on checked status
        # If checked, give it a high sort_order to move it to the bottom
        # If unchecked, give it a low sort_order to move it to the top
        if list_item.checked:
            # Get the highest sort_order in this list and add 100 to ensure it goes to the bottom
            max_sort_order = ShoppingListItem.objects.filter(
                shopping_list_id=list_id
            ).order_by('-sort_order').values_list('sort_order', flat=True).first() or 0
            list_item.sort_order = max_sort_order + 100
        else:
            # Get the lowest sort_order of unchecked items and subtract 10 to ensure it goes to the top
            min_sort_order = ShoppingListItem.objects.filter(
                shopping_list_id=list_id,
                checked=False
            ).order_by('sort_order').values_list('sort_order', flat=True).first() or 0
            list_item.sort_order = min_sort_order - 10
        
        list_item.save()
        
        return JsonResponse({
            'success': True,
            'checked': list_item.checked
        })

class UpdateListItemPriceView(LoginRequiredMixin, View):
    """Update a list item's price"""
    
    def post(self, request, list_id, item_id):
        # Get the list item and verify permissions
        list_item = get_object_or_404(
            ShoppingListItem.objects.filter(
                shopping_list__family__members__user=request.user,
                shopping_list_id=list_id
            ),
            pk=item_id
        )
        
        try:
            price = float(request.POST.get('price', 0))
            
            # Update item price
            list_item.actual_price = price
            list_item.save()
            
            # If this item has store info, update the last price there too
            try:
                item_store_info = ItemStoreInfo.objects.get(
                    item=list_item.item,
                    store=list_item.shopping_list.store
                )
                item_store_info.last_price = price
                item_store_info.last_purchased = timezone.now()
                
                # Update average price
                if item_store_info.average_price:
                    item_store_info.average_price = (item_store_info.average_price + price) / 2
                else:
                    item_store_info.average_price = price
                    
                item_store_info.save()
            except ItemStoreInfo.DoesNotExist:
                # Create new store info if it doesn't exist
                store_info = ItemStoreInfo.objects.create(
                    item=list_item.item,
                    store=list_item.shopping_list.store,
                    last_price=price,
                    average_price=price,
                    last_purchased=timezone.now()
                )
                
                # Set the location based on the item's category
                from .store_utils import find_matching_store_location
                matching_location = find_matching_store_location(list_item.item, list_item.shopping_list.store)
                if matching_location:
                    store_info.location = matching_location
                    store_info.save()
            
            return JsonResponse({
                'success': True,
                'price': price
            })
            
        except ValueError:
            return JsonResponse({'error': 'Invalid price'}, status=400)

class GetListItemLocationView(LoginRequiredMixin, View):
    """Get a list item's current location"""
    
    def get(self, request, list_id, item_id):
        # Get the list item and verify permissions
        list_item = get_object_or_404(
            ShoppingListItem.objects.filter(
                shopping_list__family__members__user=request.user,
                shopping_list_id=list_id
            ).select_related('item', 'shopping_list'),
            pk=item_id
        )
        
        try:
            # Get the store info for this item in this store
            store_info = ItemStoreInfo.objects.filter(
                item=list_item.item,
                store=list_item.shopping_list.store
            ).select_related('location').first()
            
            if store_info and store_info.location:
                return JsonResponse({
                    'success': True,
                    'location_id': store_info.location.id,
                    'location_name': store_info.location.name
                })
            else:
                return JsonResponse({
                    'success': True,
                    'location_id': None,
                    'location_name': None
                })
            
        except Exception as e:
            return JsonResponse({'error': str(e), 'success': False}, status=400)


class UpdateListItemLocationView(LoginRequiredMixin, View):
    """Update a list item's location"""
    
    def post(self, request, list_id, item_id):
        # Get the list item and verify permissions
        list_item = get_object_or_404(
            ShoppingListItem.objects.filter(
                shopping_list__family__members__user=request.user,
                shopping_list_id=list_id
            ).select_related('item', 'shopping_list', 'shopping_list__store'),
            pk=item_id
        )
        
        try:
            location_id = request.POST.get('location_id')
            
            # Get the store info for this item in this store
            store_info, created = ItemStoreInfo.objects.get_or_create(
                item=list_item.item,
                store=list_item.shopping_list.store
            )
            
            # If this is a new association and no location is specified,
            # try to set it based on the item's category
            if created and not location_id:
                from .store_utils import find_matching_store_location
                matching_location = find_matching_store_location(list_item.item, list_item.shopping_list.store)
                if matching_location:
                    location_id = str(matching_location.id)
            
            # Update the location
            location = None
            if location_id:
                location = StoreLocation.objects.get(
                    id=location_id,
                    store=list_item.shopping_list.store
                )
                store_info.location = location
            else:
                store_info.location = None
                
            store_info.save()
            
            return JsonResponse({
                'success': True,
                'location_id': location_id,
                'location_name': location.name if location else 'None'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class UpdateListItemQuantityView(LoginRequiredMixin, View):
    """Update a list item's quantity"""
    
    def post(self, request, list_id, item_id):
        # Get the list item and verify permissions
        list_item = get_object_or_404(
            ShoppingListItem.objects.filter(
                shopping_list__family__members__user=request.user,
                shopping_list_id=list_id
            ),
            pk=item_id
        )
        
        try:
            quantity = float(request.POST.get('quantity', 1))
            
            # Update item quantity
            list_item.quantity = quantity
            list_item.save()
            
            return JsonResponse({
                'success': True,
                'quantity': quantity
            })
            
        except ValueError:
            return JsonResponse({'error': 'Invalid quantity'}, status=400)
            
class UpdateListItemNoteView(LoginRequiredMixin, View):
    """Update a list item's note"""
    
    def post(self, request, list_id, item_id):
        # Get the list item and verify permissions
        list_item = get_object_or_404(
            ShoppingListItem.objects.filter(
                shopping_list__family__members__user=request.user,
                shopping_list_id=list_id
            ),
            pk=item_id
        )
        
        try:
            note = request.POST.get('note', '')
            
            # Update item note
            list_item.note = note
            list_item.save()
            
            return JsonResponse({
                'success': True,
                'note': note
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
class RemoveListItemView(LoginRequiredMixin, View):
    """Remove an item from a shopping list"""
    
    def post(self, request, list_id, item_id):
        # Get the list item and verify permissions
        list_item = get_object_or_404(
            ShoppingListItem.objects.filter(
                shopping_list__family__members__user=request.user,
                shopping_list_id=list_id
            ),
            pk=item_id
        )
        
        # Delete the item
        list_item.delete()
        
        return JsonResponse({
            'success': True
        })

# Family Views
class FamilyListView(LoginRequiredMixin, ListView):
    model = Family
    template_name = 'groceries/family/list.html'
    context_object_name = 'families'
    
    def get_queryset(self):
        return Family.objects.filter(
            members__user=self.request.user
        ).distinct()

class FamilyDetailView(LoginRequiredMixin, DetailView):
    model = Family
    template_name = 'groceries/family/detail.html'
    context_object_name = 'family'
    
    def get_queryset(self):
        return Family.objects.filter(
            members__user=self.request.user
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current user's membership
        context['user_membership'] = self.object.members.get(user=self.request.user)
        
        # Get family members
        context['members'] = self.object.members.select_related('user')
        
        # Get family lists
        context['recent_lists'] = ShoppingList.objects.filter(
            family=self.object
        ).order_by('-created_at')[:5]
        
        # Get family stores
        context['stores'] = self.object.stores.all()
        
        return context

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

class FamilyUpdateView(LoginRequiredMixin, UpdateView):
    model = Family
    form_class = FamilyForm
    template_name = 'groceries/family/edit.html'
    context_object_name = 'family'
    
    def get_queryset(self):
        # Only family admins can edit family details
        return Family.objects.filter(
            members__user=self.request.user,
            members__is_admin=True
        )
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Family "{form.instance.name}" updated successfully')
        return response
    
    def get_success_url(self):
        return reverse('groceries:family_detail', kwargs={'pk': self.object.pk})

# Store Views
class StoreListView(LoginRequiredMixin, ListView):
    model = GroceryStore
    template_name = 'groceries/stores/list.html'
    context_object_name = 'stores'
    
    def get_queryset(self):
        return GroceryStore.objects.filter(
            families__members__user=self.request.user
        ).distinct()

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

class StoreCreateView(LoginRequiredMixin, CreateView):
    model = GroceryStore
    form_class = GroceryStoreForm
    template_name = 'groceries/stores/create.html'

    def form_valid(self, form):
        # Check if we have a logo_url in the request
        logo_url = self.request.POST.get('logo_url', '')

        try:
            # Save the model first
            response = super().form_valid(form)

            # Add this store to the user's families
            family_ids = self.request.POST.getlist('families[]')

            # If we didn't get any values with families[], try the standard name
            if not family_ids:
                family_ids = self.request.POST.getlist('families')

            # Convert string IDs to integers
            family_ids = [int(id) for id in family_ids if id.isdigit()]

            families = Family.objects.filter(
                id__in=family_ids,
                members__user=self.request.user
            )

            if families:
                self.object.families.add(*families)

            # Download and save logo if a URL was provided and no logo was uploaded
            if logo_url and not self.object.logo:
                save_store_logo_from_url(self.object, logo_url)

            # Create default store locations
            locations = create_default_store_locations(self.object)

            messages.success(
                self.request,
                f'Store "{form.instance.name}" created successfully with {len(locations)} default store locations. '
                f'You can customize them in the store details page.'
            )
            return response
            
        except IntegrityError as e:
            # Handle duplicate slug error
            if 'duplicate key value violates unique constraint' in str(e) and 'slug' in str(e):
                # Get store that caused conflict
                existing_slug = slugify(form.instance.name)
                try:
                    existing_store = GroceryStore.objects.get(slug=existing_slug)
                    messages.error(
                        self.request,
                        f'A store with the name "{existing_store.name}" already exists. '
                        f'Please use a different name or edit the existing store.'
                    )
                except GroceryStore.DoesNotExist:
                    # General error message if we can't find the specific store
                    messages.error(
                        self.request,
                        f'A store with a similar name already exists. Please use a different name.'
                    )
                
                # Return to form with errors
                return self.form_invalid(form)
            else:
                # Re-raise the exception for other IntegrityErrors
                raise
    
    def get_success_url(self):
        return reverse('groceries:store_detail', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['families'] = Family.objects.filter(
            members__user=self.request.user
        ).distinct()

        # Get default family (or first family if no default set)
        user_profile = self.request.user.profile
        if user_profile.default_family:
            context['default_family'] = user_profile.default_family
        elif context['families'].exists():
            context['default_family'] = context['families'].first()
        else:
            context['default_family'] = None

        return context

class StoreUpdateView(LoginRequiredMixin, UpdateView):
    model = GroceryStore
    form_class = GroceryStoreForm
    template_name = 'groceries/stores/edit.html'
    context_object_name = 'store'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Update store families
        family_ids = self.request.POST.getlist('families[]')
        
        # If we didn't get any values with families[], try the standard name
        if not family_ids:
            family_ids = self.request.POST.getlist('families')
            
        # Convert string IDs to integers
        family_ids = [int(id) for id in family_ids if id.isdigit()]
        
        # Clear existing families and add selected ones
        self.object.families.clear()
        
        families = Family.objects.filter(
            id__in=family_ids,
            members__user=self.request.user
        )
        
        if families:
            self.object.families.add(*families)
            
        messages.success(self.request, f'Store "{form.instance.name}" updated successfully')
        return response
    
    def get_queryset(self):
        return GroceryStore.objects.filter(
            families__members__user=self.request.user
        ).distinct()
        self.object.families.add(*families)
        
        messages.success(self.request, f'Store "{form.instance.name}" updated successfully')
        return response
    
    def get_success_url(self):
        return reverse('groceries:store_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['families'] = Family.objects.filter(
            members__user=self.request.user
        ).distinct()
        return context

# API Views for search and recommendations
class GroceryItemSearchView(LoginRequiredMixin, View):
    """Search for grocery items for a specific family/store"""
    
    def get(self, request):
        family_id = request.GET.get('family')
        store_id = request.GET.get('store')
        query = request.GET.get('query', '').strip()

        # If no family_id specified, try to use the user's default family
        if not family_id:
            try:
                user_profile = request.user.profile
                if user_profile.default_family:
                    family_id = user_profile.default_family.id
                else:
                    # Get the first family user belongs to
                    family_membership = request.user.family_memberships.first()
                    if family_membership:
                        family_id = family_membership.family.id
            except Exception as e:
                print(f"Error getting default family: {e}")

        if not family_id:
            return JsonResponse({'error': 'Family ID is required. Please set a default family in your profile.'}, status=400)
        
        try:
            family = Family.objects.get(id=family_id)
            
            # Check if user belongs to this family
            if not request.user.family_memberships.filter(family=family).exists():
                return JsonResponse({'error': 'You do not have permission to access this family'}, status=403)
            
            store = None
            if store_id:
                store = GroceryStore.objects.get(id=store_id)
            
            if query:
                # Search for items by name/brand matching the query (case insensitive)
                items = GroceryItem.objects.filter(
                    Q(name__icontains=query) | 
                    Q(brand__icontains=query) |
                    Q(description__icontains=query) |
                    Q(category__name__icontains=query)
                ).distinct()
                
                if store:
                    # Use a left outer join to include items without store info
                    items = items.filter(
                        Q(store_info__store=store) | Q(store_info__isnull=True)
                    )
                
                # Log the query and result count for debugging
                print(f"DEBUG: Search query '{query}' for family {family.id}, found initial count: {items.count()}")
                
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
            
            print(f"Search for '{query}' found {len(items_data)} items")  # Debug output
            return JsonResponse({'items': items_data})
            
        except (Family.DoesNotExist, GroceryStore.DoesNotExist):
            return JsonResponse({'error': 'Invalid family or store ID'}, status=400)

# User Profile Views
class UserProfileView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = 'groceries/profile/detail.html'
    context_object_name = 'profile'
    
    def get_object(self, queryset=None):
        # Get or create profile for current user
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['families'] = Family.objects.filter(
            members__user=self.request.user
        )
        
        return context

class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'groceries/profile/edit.html'
    context_object_name = 'profile'
    success_url = reverse_lazy('groceries:profile')
    
    def get_object(self, queryset=None):
        # Get or create profile for current user
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Profile updated successfully')
        return response

# Offline View
class LandingPageView(TemplateView):
    template_name = 'landing.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('groceries:dashboard')
        return super().dispatch(request, *args, **kwargs)

class OfflineView(TemplateView):
    template_name = 'groceries/offline.html'

class BarcodeSearchView(LoginRequiredMixin, View):
    """API endpoint to search for items by barcode"""
    
    def get(self, request, barcode):
        try:
            # First try to find the item in our database
            item = GroceryItem.objects.filter(barcode=barcode).first()
            
            if item:
                # Item found in our database
                return JsonResponse({
                    'found': True,
                    'id': item.id,
                    'name': item.name,
                    'brand': item.brand or '',
                    'category': item.category.name if item.category else '',
                    'image_url': item.image_url or ''
                })
            
            # If not found locally, try Open Food Facts API
            # This is an example of how to query the Open Food Facts API
            # In a real implementation, you would want to handle API errors, rate limiting, etc.
            import requests
            response = requests.get(f'https://world.openfoodfacts.org/api/v0/product/{barcode}.json')
            data = response.json()
            
            if data.get('status') == 1:
                # Product found in Open Food Facts
                product = data.get('product', {})
                
                # Extract relevant data
                name = product.get('product_name', '')
                brand = product.get('brands', '')
                category_tag = product.get('categories_tags', [''])[0] if product.get('categories_tags') else ''
                image_url = product.get('image_url', '')
                
                # Find or create a category
                category = None
                if category_tag:
                    # Convert category tag to a readable name
                    category_name = category_tag.replace('en:', '').replace('-', ' ').title()
                    
                    # Find or create the category
                    category, _ = ProductCategory.objects.get_or_create(
                        name=category_name
                    )
                
                # Create the item in our database
                item = GroceryItem.objects.create(
                    name=name,
                    brand=brand,
                    category=category,
                    barcode=barcode,
                    image_url=image_url,
                    is_verified=True,  # This is from a verified source
                    off_id=data.get('code'),  # Store the Open Food Facts ID
                    created_by=None  # System-created item
                )
                
                return JsonResponse({
                    'found': True,
                    'id': item.id,
                    'name': item.name,
                    'brand': item.brand or '',
                    'category': item.category.name if item.category else '',
                    'image_url': item.image_url or ''
                })
            
            # Product not found anywhere
            return JsonResponse({
                'found': False,
                'barcode': barcode
            })
            
        except Exception as e:
            return JsonResponse({
                'found': False,
                'error': str(e),
                'barcode': barcode
            }, status=500)

class InviteFamilyMemberView(LoginRequiredMixin, View):
    """View for inviting family members"""
    
    def post(self, request, pk):
        try:
            # Get the family and ensure the user is an admin
            family = get_object_or_404(
                Family, 
                id=pk,
                members__user=request.user,
                members__is_admin=True
            )
            
            # Get form data
            email = request.POST.get('email')
            is_admin = request.POST.get('is_admin') == 'on'
            
            if not email:
                messages.error(request, 'Email address is required')
                return redirect('groceries:family_detail', pk=family.id)
            
            # Check if the user exists
            try:
                user = User.objects.get(email=email)
                
                # Check if already a member
                if FamilyMember.objects.filter(user=user, family=family).exists():
                    messages.warning(request, f'{email} is already a member of this family')
                    return redirect('groceries:family_detail', pk=family.id)
                
                # Add as family member
                FamilyMember.objects.create(
                    user=user,
                    family=family,
                    is_admin=is_admin
                )
                
                messages.success(request, f'{email} has been added to your family')
                
            except User.DoesNotExist:
                # User doesn't exist - in a real app, you would send an invitation email
                # For now, just show a message
                messages.info(request, f'Invitation sent to {email}')
                
                # TODO: Implement invitation system
                # This would involve:
                # 1. Creating an Invitation model
                # 2. Generating a unique invitation token
                # 3. Sending an email with a link to register/accept
                # 4. Creating a view to handle the acceptance
                
            return redirect('groceries:family_detail', pk=family.id)
                
        except Exception as e:
            messages.error(request, f'Error inviting member: {str(e)}')
            return redirect('groceries:family_detail', pk=family.id)


class UpdateFamilyMemberView(LoginRequiredMixin, View):
    """Update family member admin status"""
    
    def post(self, request, pk, member_pk):
        try:
            # Get the family and ensure the user is an admin
            family = get_object_or_404(
                Family, 
                id=pk,
                members__user=request.user,
                members__is_admin=True
            )
            
            # Get the member to update
            member = get_object_or_404(FamilyMember, id=member_pk, family=family)
            
            # Don't allow users to modify their own admin status
            if member.user == request.user:
                messages.error(request, "You cannot modify your own admin status")
                return redirect('groceries:family_detail', pk=family.id)
            
            # Update admin status
            is_admin = request.POST.get('is_admin') == 'true'
            member.is_admin = is_admin
            member.save()
            
            action = "made an admin" if is_admin else "removed as admin"
            messages.success(
                request, 
                f"{member.user.get_full_name() or member.user.username} {action} successfully"
            )
            
            return redirect('groceries:family_detail', pk=family.id)
                
        except Exception as e:
            messages.error(request, f'Error updating member: {str(e)}')
            return redirect('groceries:family_detail', pk=family.id)


class RemoveFamilyMemberView(LoginRequiredMixin, View):
    """Remove a member from a family"""
    
    def post(self, request, pk, member_pk):
        try:
            # Get the family and ensure the user is an admin
            family = get_object_or_404(
                Family, 
                id=pk,
                members__user=request.user,
                members__is_admin=True
            )
            
            # Get the member to remove
            member = get_object_or_404(FamilyMember, id=member_pk, family=family)
            
            # Don't allow users to remove themselves
            if member.user == request.user:
                messages.error(request, "You cannot remove yourself from the family. Transfer ownership first.")
                return redirect('groceries:family_detail', pk=family.id)
            
            # Store the name for the success message
            member_name = member.user.get_full_name() or member.user.username
            
            # Remove the member
            member.delete()
            
            messages.success(request, f"{member_name} removed from family successfully")
            return redirect('groceries:family_detail', pk=family.id)
                
        except Exception as e:
            messages.error(request, f'Error removing member: {str(e)}')
            return redirect('groceries:family_detail', pk=family.id)

# ToggleCategoriesView removed - using flat list only

class UpdateThemeView(LoginRequiredMixin, View):
    """API endpoint to update user theme preference and default family"""

    def post(self, request):
        try:
            # Process dark mode update
            if 'dark_mode' in request.POST:
                dark_mode = request.POST.get('dark_mode') == 'true'

                # Get or create user profile
                profile, created = UserProfile.objects.get_or_create(user=request.user)

                # Update theme preference
                profile.dark_mode = dark_mode
                profile.save(update_fields=['dark_mode'])

                return JsonResponse({
                    'success': True,
                    'dark_mode': dark_mode
                })
                
            # Process default family update
            elif 'default_family' in request.POST:
                family_id = request.POST.get('default_family')
                
                try:
                    # Verify this family exists and user is a member
                    family = Family.objects.get(
                        id=family_id,
                        members__user=request.user
                    )
                    
                    # Update profile with new default family
                    profile, created = UserProfile.objects.get_or_create(user=request.user)
                    profile.default_family = family
                    profile.save(update_fields=['default_family'])
                    
                    messages.success(request, f'"{family.name}" set as your default family')
                    
                    # Redirect back to families page
                    return redirect('groceries:family')
                
                except Family.DoesNotExist:
                    messages.error(request, "That family doesn't exist or you don't have access to it")
                    return redirect('groceries:family')
            
            # No valid action found
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No valid action specified'
                }, status=400)

        except Exception as e:
            if 'default_family' in request.POST:
                messages.error(request, f"Error setting default family: {str(e)}")
                return redirect('groceries:family')
            else:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)

class StoreSearchView(LoginRequiredMixin, View):
    """API endpoint to search for store information"""

    def get(self, request):
        query = request.GET.get('query', '').strip()

        if not query:
            # Return popular stores if no query
            stores = get_common_store_data()[:6]
            return JsonResponse({
                'success': True,
                'stores': stores
            })

        try:
            # Search for store info
            store_info = search_store_info(query)

            return JsonResponse({
                'success': True,
                'store': store_info
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class GroceryItemCreateView(LoginRequiredMixin, CreateView):
    model = GroceryItem
    form_class = GroceryItemForm
    template_name = 'groceries/items/create.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Set the created_by field to the current user
        form.instance.created_by = self.request.user
        form.instance.is_user_added = True
        
        # Get family ID from query parameter if present
        family_id = self.request.GET.get('family')
        list_id = self.request.GET.get('list')
        
        response = super().form_valid(form)
        
        # If family ID is provided, associate the item with that family
        if family_id:
            try:
                family = Family.objects.get(id=family_id, members__user=self.request.user)
                FamilyItemUsage.objects.create(
                    family=family,
                    item=self.object,
                    usage_count=1
                )
            except Family.DoesNotExist:
                pass
        
        # If list ID is provided, add the item to that list and redirect to the list detail page
        if list_id:
            try:
                shopping_list = ShoppingList.objects.get(
                    id=list_id,
                    family__members__user=self.request.user
                )
                
                # Create list item
                ShoppingListItem.objects.create(
                    shopping_list=shopping_list,
                    item=self.object,
                    quantity=1
                )
                
                messages.success(self.request, f'"{self.object.name}" added to list')
                return redirect('groceries:list_detail', pk=shopping_list.id)
                
            except ShoppingList.DoesNotExist:
                pass
        
        messages.success(self.request, f'Item "{self.object.name}" created successfully')
        return response
    
    def get_success_url(self):
        # If redirecting to list detail view, this won't be used
        return reverse('groceries:item_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get list info if provided
        list_id = self.request.GET.get('list')
        if list_id:
            try:
                shopping_list = ShoppingList.objects.get(
                    id=list_id,
                    family__members__user=self.request.user
                )
                context['shopping_list'] = shopping_list
            except ShoppingList.DoesNotExist:
                pass
        
        # Get categories for dropdown
        context['categories'] = ProductCategory.objects.all().order_by('name')
        
        return context

class GroceryItemDetailView(LoginRequiredMixin, DetailView):
    model = GroceryItem
    template_name = 'groceries/items/detail.html'
    context_object_name = 'item'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get store-specific information
        context['store_info'] = ItemStoreInfo.objects.filter(
            item=self.object
        ).select_related('store', 'location')
        
        # Get family usage information
        context['family_usage'] = FamilyItemUsage.objects.filter(
            item=self.object,
            family__members__user=self.request.user
        ).select_related('family')
        
        # Get lists that contain this item
        context['lists'] = ShoppingList.objects.filter(
            items__item=self.object,
            family__members__user=self.request.user
        ).distinct()
        
        return context

class GroceryItemListView(LoginRequiredMixin, ListView):
    model = GroceryItem
    template_name = 'groceries/items/list.html'
    context_object_name = 'items'
    paginate_by = 20
    
    def get_queryset(self):
        # Filter query by search term if provided
        search_term = self.request.GET.get('search', '')
        
        # Start with basic queryset filtering for items accessible to the user
        queryset = GroceryItem.objects.filter(
            Q(created_by=self.request.user) | 
            Q(families__members__user=self.request.user)
        )
        
        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(brand__icontains=search_term) |
                Q(category__name__icontains=search_term)
            )
            
        # Annotate the queryset with lowest price info
        # First, get user's accessible stores
        user_families = Family.objects.filter(members__user=self.request.user)
        accessible_stores = GroceryStore.objects.filter(
            families__in=user_families
        ).distinct()
        
        # Add annotations for lowest price and associated store
        from django.db.models import Min, OuterRef, Subquery
        
        # Subquery to find the lowest price for each item
        # This complex query handles cases where typical_price might be NULL
        # by falling back to last_price or average_price
        from django.db.models.functions import Coalesce
        
        store_info_subquery = ItemStoreInfo.objects.filter(
            item=OuterRef('pk'),
            store__in=accessible_stores
        ).annotate(
            effective_price=Coalesce('typical_price', 'last_price', 'average_price')
        ).exclude(
            effective_price__isnull=True
        ).order_by('effective_price')
        
        queryset = queryset.annotate(
            lowest_price=Subquery(
                store_info_subquery.values('effective_price')[:1]
            ),
            lowest_price_store_id=Subquery(
                store_info_subquery.values('store__id')[:1]
            ),
            lowest_price_store_name=Subquery(
                store_info_subquery.values('store__name')[:1]
            )
        )
            
        return queryset.distinct().order_by('name')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        context['categories'] = ProductCategory.objects.all().order_by('name')
        
        # Get stores the user has access to
        user_families = Family.objects.filter(members__user=self.request.user)
        context['stores'] = GroceryStore.objects.filter(
            families__in=user_families
        ).distinct()
        
        return context

class ItemStoreLocationView(LoginRequiredMixin, UpdateView):
    """View for managing an item's store locations"""
    model = GroceryItem
    template_name = 'groceries/items/store_locations.html'
    context_object_name = 'item'
    fields = []  # No fields to update on the item itself
    
    def get_queryset(self):
        # Users can only manage items they created or items used by their families
        return GroceryItem.objects.filter(
            Q(created_by=self.request.user) | 
            Q(families__members__user=self.request.user)
        ).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get stores the user has access to
        user_families = Family.objects.filter(members__user=self.request.user)
        stores = GroceryStore.objects.filter(
            families__in=user_families
        ).distinct()
        
        # Get store info for this item
        store_info = {}
        for store in stores:
            # Get or initialize store info for this item
            info, created = ItemStoreInfo.objects.get_or_create(
                item=self.object,
                store=store
            )
            
            # If this is a new association and the item doesn't have a location yet,
            # try to set it based on the item's category
            if created and not info.location:
                from .store_utils import find_matching_store_location
                matching_location = find_matching_store_location(self.object, store)
                if matching_location:
                    info.location = matching_location
                    info.save()
            
            # Get store locations
            locations = StoreLocation.objects.filter(store=store).order_by('sort_order', 'name')
            
            store_info[store] = {
                'info': info,
                'locations': locations
            }
        
        context['store_info'] = store_info
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Get form data
        store_id = request.POST.get('store_id')
        location_id = request.POST.get('location_id', '')
        
        try:
            # Get the store
            store = GroceryStore.objects.get(id=store_id)
            
            # Get or create store info
            store_info, created = ItemStoreInfo.objects.get_or_create(
                item=self.object,
                store=store
            )
            
            # If this is a new association and no location is being explicitly set,
            # try to set it based on the item's category
            if created and not location_id:
                from .store_utils import find_matching_store_location
                matching_location = find_matching_store_location(self.object, store)
                if matching_location:
                    location_id = matching_location.id
                    location = matching_location
            
            # Set location (or None to remove it)
            if location_id:
                location = StoreLocation.objects.get(id=location_id, store=store)
                store_info.location = location
            else:
                store_info.location = None
                
            store_info.save()
            
            messages.success(request, f"Updated location for {self.object.name} in {store.name}")
        except (GroceryStore.DoesNotExist, StoreLocation.DoesNotExist):
            messages.error(request, "Invalid store or location selected")
            
        return redirect('groceries:item_store_locations', pk=self.object.pk)
    
    def get_success_url(self):
        return reverse('groceries:item_store_locations', kwargs={'pk': self.object.pk})

class GroceryItemDeleteView(LoginRequiredMixin, DeleteView):
    """View for deleting a grocery item"""
    model = GroceryItem
    template_name = 'groceries/items/confirm_delete.html'
    context_object_name = 'item'
    success_url = reverse_lazy('groceries:items')
    
    def get_queryset(self):
        # Users can only delete items they created
        return GroceryItem.objects.filter(
            Q(created_by=self.request.user) | 
            Q(families__members__user=self.request.user, families__members__is_admin=True)
        ).distinct()
    
    def delete(self, request, *args, **kwargs):
        item = self.get_object()
        item_name = item.name
        
        # Check if item is used in any shopping lists
        list_items = ShoppingListItem.objects.filter(item=item)
        if list_items.exists():
            messages.warning(request, f'Cannot delete "{item_name}" as it is used in {list_items.count()} shopping lists')
            return redirect('groceries:item_detail', pk=item.id)
        
        # If not used in lists, proceed with deletion
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Product "{item_name}" has been deleted')
        return response

class GroceryItemUpdateView(LoginRequiredMixin, UpdateView):
    model = GroceryItem
    form_class = GroceryItemForm
    template_name = 'groceries/items/edit.html'
    context_object_name = 'item'
    
    def get_queryset(self):
        # Users can only edit items they created or items used by their families
        return GroceryItem.objects.filter(
            Q(created_by=self.request.user) | 
            Q(families__members__user=self.request.user)
        ).distinct()
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Item "{form.instance.name}" updated successfully')
        return response
    
    def get_success_url(self):
        return reverse('groceries:item_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get categories for dropdown
        context['categories'] = ProductCategory.objects.all().order_by('name')
        
        return context


class UserRegistrationView(CreateView):
    """View for user registration"""
    form_class = UserRegistrationForm
    template_name = 'groceries/auth/register.html'
    success_url = reverse_lazy('login')
    
    def dispatch(self, request, *args, **kwargs):
        # Redirect to dashboard if user is already authenticated
        if request.user.is_authenticated:
            return redirect('groceries:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Create a default family for the new user
        family = Family.objects.create(
            name=f"{self.object.username}'s Family",
            created_by=self.object
        )
        
        # Add the user as a family member and admin
        FamilyMember.objects.create(
            user=self.object,
            family=family,
            is_admin=True
        )
        
        # Set this as the default family in their profile
        profile = self.object.profile
        profile.default_family = family
        profile.save()

        messages.success(self.request, "Your account has been created successfully! You can now log in.")
        return response

# We'll import store_utils in shop_smart/urls.py directly to avoid circular imports