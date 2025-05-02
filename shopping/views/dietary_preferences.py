from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ..allergens import COMMON_ALLERGENS, DIETARY_PREFERENCES, AllergenDetector
from ..models import UserProfile, GroceryItem

@login_required
def dietary_preferences_view(request):
    """Display and manage user's dietary preferences"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user's current preferences
    user_allergens = profile.get_allergens()
    user_preferences = profile.get_preferences()
    
    context = {
        'common_allergens': COMMON_ALLERGENS,
        'dietary_preferences': DIETARY_PREFERENCES,
        'user_allergens': user_allergens,
        'user_preferences': user_preferences
    }
    
    return render(request, 'shopping/profile/dietary_preferences.html', context)

@login_required
@require_POST
def update_allergens(request):
    """Update user's allergen preferences"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get allergens from form
    allergens = request.POST.getlist('allergens')
    
    # Update profile
    profile.set_allergens(allergens)
    
    messages.success(request, 'Allergen preferences updated successfully')
    return redirect('groceries:dietary_preferences')

@login_required
@require_POST
def update_preferences(request):
    """Update user's dietary preferences"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get preferences from form
    preferences = request.POST.getlist('preferences')
    
    # Update profile
    profile.set_preferences(preferences)
    
    messages.success(request, 'Dietary preferences updated successfully')
    return redirect('groceries:dietary_preferences')

@login_required
def check_product_safety(request, product_id):
    """API endpoint to check if a product is safe based on user preferences"""
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        product = GroceryItem.objects.get(id=product_id)
        
        # Get user's preferences
        user_allergens = profile.get_allergens()
        user_preferences = profile.get_preferences()
        
        # Check if product is safe
        product_data = {
            'ingredients': product.description,
            'allergens': []  # You'd need to add this field to your model or get from Open Food Facts
        }
        
        safety_result = AllergenDetector.is_safe_for_user(
            product_data, 
            user_allergens=user_allergens, 
            user_preferences=user_preferences
        )
        
        return JsonResponse(safety_result)
        
    except GroceryItem.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def filter_products(request):
    """
    API endpoint to filter a list of products based on user preferences
    Expects query parameters:
    - product_ids: comma-separated list of product IDs
    - include_unsafe: whether to include unsafe products in the response
    """
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Get product IDs from query params
        product_ids_param = request.GET.get('product_ids', '')
        if not product_ids_param:
            return JsonResponse({'error': 'No product IDs provided'}, status=400)
        
        # Convert to list of integers
        product_ids = [int(pid.strip()) for pid in product_ids_param.split(',') if pid.strip().isdigit()]
        
        # Get include_unsafe parameter
        include_unsafe = request.GET.get('include_unsafe', 'false').lower() == 'true'
        
        # Get user's preferences
        user_allergens = profile.get_allergens()
        user_preferences = profile.get_preferences()
        
        # If user has no preferences, all products are safe
        if not user_allergens and not user_preferences:
            products = GroceryItem.objects.filter(id__in=product_ids)
            return JsonResponse({
                'safe_products': [p.id for p in products],
                'unsafe_products': [],
                'unknown_safety_products': []
            })
        
        # Get products from database
        products = GroceryItem.objects.filter(id__in=product_ids)
        
        # Prepare product data for filtering
        product_data_list = []
        for product in products:
            product_data_list.append({
                'id': product.id,
                'ingredients': product.description,
                'allergens': []  # You'd need to add this field to your model
            })
        
        # Filter products
        safe_products, unsafe_products, unknown_safety_products = AllergenDetector.filter_products(
            product_data_list,
            user_allergens=user_allergens,
            user_preferences=user_preferences
        )
        
        # Return filtered product IDs
        result = {
            'safe_products': [p['id'] for p in safe_products],
            'unsafe_products': [p['id'] for p in unsafe_products],
            'unknown_safety_products': [p['id'] for p in unknown_safety_products]
        }
        
        # If include_unsafe is true, add a combined list of all products
        if include_unsafe:
            result['all_products'] = product_ids
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)