import re
from difflib import SequenceMatcher
from typing import List, Dict, Tuple, Optional
from django.db.models import Q
from .models import GroceryItem, ProductCategory


def parse_item_text(item_text: str) -> Dict[str, str]:
    """
    Parse item text to extract quantity, unit, and item name.
    
    Examples:
    - "2 apples" -> {"quantity": "2", "unit": "", "name": "apples"}
    - "milk 1 gallon" -> {"quantity": "1", "unit": "gallon", "name": "milk"}
    - "3 lbs ground beef" -> {"quantity": "3", "unit": "lbs", "name": "ground beef"}
    - "bananas" -> {"quantity": "1", "unit": "", "name": "bananas"}
    """
    item_text = item_text.strip()
    
    # Common units
    units = [
        'lb', 'lbs', 'pound', 'pounds', 'oz', 'ounce', 'ounces',
        'kg', 'kilogram', 'kilograms', 'g', 'gram', 'grams',
        'gallon', 'gallons', 'gal', 'quart', 'quarts', 'qt',
        'pint', 'pints', 'pt', 'cup', 'cups', 'c',
        'liter', 'liters', 'l', 'ml', 'milliliter', 'milliliters',
        'pkg', 'package', 'packages', 'pack', 'packs',
        'box', 'boxes', 'bag', 'bags', 'can', 'cans',
        'bottle', 'bottles', 'jar', 'jars', 'tube', 'tubes',
        'dozen', 'doz', 'each', 'ea'
    ]
    
    # Try to match patterns like "2 apples", "milk 1 gallon", "3 lbs ground beef"
    patterns = [
        # Pattern: "2 apples" or "2.5 apples"
        r'^(\d+(?:\.\d+)?)\s+(.+)$',
        # Pattern: "milk 1 gallon" or "ground beef 3 lbs"
        r'^(.+?)\s+(\d+(?:\.\d+)?)\s+(' + '|'.join(units) + r')\b(.*)$',
        # Pattern: "3 lbs ground beef"
        r'^(\d+(?:\.\d+)?)\s+(' + '|'.join(units) + r')\s+(.+)$',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, item_text, re.IGNORECASE)
        if match:
            groups = match.groups()
            
            if len(groups) == 2:  # "2 apples"
                return {
                    "quantity": groups[0],
                    "unit": "",
                    "name": groups[1].strip()
                }
            elif len(groups) == 4:  # "milk 1 gallon" or similar
                name_part = groups[0].strip()
                if groups[3]:  # Additional name part after unit
                    name_part += " " + groups[3].strip()
                return {
                    "quantity": groups[1],
                    "unit": groups[2],
                    "name": name_part
                }
            elif len(groups) == 3:  # "3 lbs ground beef"
                return {
                    "quantity": groups[0],
                    "unit": groups[1],
                    "name": groups[2].strip()
                }
    
    # No pattern matched, return as-is with default quantity
    return {
        "quantity": "1",
        "unit": "",
        "name": item_text
    }


def similarity(a: str, b: str) -> float:
    """Calculate similarity between two strings using SequenceMatcher."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def fuzzy_match_items(item_names: List[str], threshold: float = 0.6) -> Dict[str, List[Dict]]:
    """
    Fuzzy match a list of item names against existing grocery items.
    
    Returns a dictionary with:
    - 'found': List of items that were matched
    - 'not_found': List of items that couldn't be matched
    """
    results = {
        'found': [],
        'not_found': []
    }
    
    # Get all existing items
    existing_items = GroceryItem.objects.all().values('id', 'name', 'brand', 'category__name')
    
    for item_name in item_names:
        item_name = item_name.strip()
        if not item_name:
            continue
            
        best_match = None
        best_score = 0
        
        # Search for exact matches first
        exact_matches = GroceryItem.objects.filter(
            Q(name__iexact=item_name) |
            Q(name__icontains=item_name)
        ).values('id', 'name', 'brand', 'category__name')
        
        if exact_matches:
            best_match = exact_matches[0]
            best_score = 1.0
        else:
            # Fuzzy matching
            for existing_item in existing_items:
                # Compare with item name
                score = similarity(item_name, existing_item['name'])
                
                # Also compare with brand + name if brand exists
                if existing_item['brand']:
                    brand_name_score = similarity(item_name, f"{existing_item['brand']} {existing_item['name']}")
                    score = max(score, brand_name_score)
                
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = existing_item
        
        if best_match:
            results['found'].append({
                'input_name': item_name,
                'matched_item': best_match,
                'score': best_score
            })
        else:
            results['not_found'].append({
                'input_name': item_name,
                'suggested_name': item_name.title(),
                'suggested_category': suggest_category(item_name)
            })
    
    return results


def suggest_category(item_name: str) -> Optional[Dict]:
    """Suggest a category for an item based on keywords."""
    item_name_lower = item_name.lower()
    
    # Category keywords mapping
    category_keywords = {
        'produce': ['apple', 'banana', 'orange', 'lettuce', 'tomato', 'onion', 'potato', 'carrot', 'broccoli', 'spinach', 'fruit', 'vegetable'],
        'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'sour cream', 'cottage cheese'],
        'meat': ['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'turkey', 'ham', 'bacon', 'sausage'],
        'bakery': ['bread', 'bagel', 'muffin', 'croissant', 'cake', 'cookie', 'pie', 'donut'],
        'frozen': ['frozen', 'ice cream', 'frozen pizza', 'frozen vegetables'],
        'beverages': ['juice', 'soda', 'water', 'coffee', 'tea', 'wine', 'beer'],
        'pantry': ['rice', 'pasta', 'cereal', 'sauce', 'oil', 'vinegar', 'salt', 'pepper', 'sugar', 'flour'],
        'household': ['detergent', 'soap', 'shampoo', 'toothpaste', 'toilet paper', 'paper towel']
    }
    
    for category_name, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in item_name_lower:
                try:
                    category = ProductCategory.objects.filter(name__icontains=category_name).first()
                    if category:
                        return {'id': category.id, 'name': category.name}
                except:
                    pass
    
    # Return a default category if no match found
    try:
        default_category = ProductCategory.objects.filter(name__icontains='other').first()
        if default_category:
            return {'id': default_category.id, 'name': default_category.name}
    except:
        pass
    
    return None


def parse_bulk_import_text(text: str) -> List[Dict[str, str]]:
    """
    Parse bulk import text into individual items.
    Handles both comma-separated and newline-separated items.
    """
    items = []
    
    # Split by newlines first, then by commas
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Split by commas if the line contains commas
        if ',' in line:
            comma_items = [item.strip() for item in line.split(',')]
            for item in comma_items:
                if item:
                    parsed_item = parse_item_text(item)
                    items.append(parsed_item)
        else:
            # Single item per line
            parsed_item = parse_item_text(line)
            items.append(parsed_item)
    
    return items