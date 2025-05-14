from .models import GroceryStore, StoreLocation
import os
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import urllib.request
import json

def create_default_store_locations(store):
    """Create default store locations for a newly created store."""

    # Define common store locations with reasonable sort order
    default_locations = [
        {"name": "Produce", "sort_order": 10},
        {"name": "Dairy", "sort_order": 20},
        {"name": "Meat", "sort_order": 30},
        {"name": "Seafood", "sort_order": 40},
        {"name": "Bakery", "sort_order": 50},
        {"name": "Deli", "sort_order": 60},
        {"name": "Canned Goods", "sort_order": 70},
        {"name": "Dry Goods", "sort_order": 80},
        {"name": "Pasta & Rice", "sort_order": 90},
        {"name": "Snacks", "sort_order": 100},
        {"name": "Breakfast", "sort_order": 110},
        {"name": "Baking", "sort_order": 120},
        {"name": "Condiments", "sort_order": 130},
        {"name": "Beverages", "sort_order": 140},
        {"name": "Frozen Foods", "sort_order": 150},
        {"name": "Health & Beauty", "sort_order": 160},
        {"name": "Household", "sort_order": 170},
        {"name": "Baby Products", "sort_order": 180},
        {"name": "Pet Supplies", "sort_order": 190},
        {"name": "International Foods", "sort_order": 200},
        {"name": "Specialty Foods", "sort_order": 210},
    ]

    # Create each location
    locations_created = []
    for location_data in default_locations:
        location = StoreLocation.objects.create(
            store=store,
            name=location_data["name"],
            sort_order=location_data["sort_order"]
        )
        locations_created.append(location)

    return locations_created

def get_common_store_data():
    """Returns data for common grocery stores."""
    return [
        {
            "name": "Walmart",
            "website": "https://www.walmart.com",
            "logo_url": "https://logo.clearbit.com/walmart.com",
            "address": "Varies by location"
        },
        {
            "name": "Target",
            "website": "https://www.target.com",
            "logo_url": "https://logo.clearbit.com/target.com",
            "address": "Varies by location"
        },
        {
            "name": "Kroger",
            "website": "https://www.kroger.com",
            "logo_url": "https://logo.clearbit.com/kroger.com",
            "address": "Varies by location"
        },
        {
            "name": "Safeway",
            "website": "https://www.safeway.com",
            "logo_url": "https://logo.clearbit.com/safeway.com",
            "address": "Varies by location"
        },
        {
            "name": "Whole Foods",
            "website": "https://www.wholefoodsmarket.com",
            "logo_url": "https://logo.clearbit.com/wholefoodsmarket.com",
            "address": "Varies by location"
        },
        {
            "name": "Costco",
            "website": "https://www.costco.com",
            "logo_url": "https://logo.clearbit.com/costco.com",
            "address": "Varies by location"
        },
        {
            "name": "Aldi",
            "website": "https://www.aldi.us",
            "logo_url": "https://logo.clearbit.com/aldi.us",
            "address": "Varies by location"
        },
        {
            "name": "Trader Joe's",
            "website": "https://www.traderjoes.com",
            "logo_url": "https://logo.clearbit.com/traderjoes.com",
            "address": "Varies by location"
        },
        {
            "name": "Publix",
            "website": "https://www.publix.com",
            "logo_url": "https://logo.clearbit.com/publix.com",
            "address": "Varies by location"
        },
        {
            "name": "Albertsons",
            "website": "https://www.albertsons.com",
            "logo_url": "https://logo.clearbit.com/albertsons.com",
            "address": "Varies by location"
        },
        {
            "name": "Sam's Club",
            "website": "https://www.samsclub.com",
            "logo_url": "https://logo.clearbit.com/samsclub.com",
            "address": "Varies by location"
        },
        {
            "name": "Amazon Fresh",
            "website": "https://www.amazon.com/fresh",
            "logo_url": "https://logo.clearbit.com/amazon.com",
            "address": "Online"
        },
        {
            "name": "Sprouts",
            "website": "https://www.sprouts.com",
            "logo_url": "https://logo.clearbit.com/sprouts.com",
            "address": "Varies by location"
        },
        {
            "name": "Food Lion",
            "website": "https://www.foodlion.com",
            "logo_url": "https://logo.clearbit.com/foodlion.com",
            "address": "Varies by location"
        },
        {
            "name": "Meijer",
            "website": "https://www.meijer.com",
            "logo_url": "https://logo.clearbit.com/meijer.com",
            "address": "Varies by location"
        },
        {
            "name": "Wegmans",
            "website": "https://www.wegmans.com",
            "logo_url": "https://logo.clearbit.com/wegmans.com",
            "address": "Varies by location"
        },
        {
            "name": "Fresh Thyme",
            "website": "https://www.freshthyme.com",
            "logo_url": "https://logo.clearbit.com/freshthyme.com",
            "address": "Varies by location"
        },
        {
            "name": "Giant",
            "website": "https://giantfood.com",
            "logo_url": "https://logo.clearbit.com/giantfood.com",
            "address": "Varies by location"
        },
        {
            "name": "Cub Foods",
            "website": "https://www.cub.com",
            "logo_url": "https://logo.clearbit.com/cub.com",
            "address": "Varies by location"
        },
        {
            "name": "Karns Foods",
            "website": "https://www.karnsfoods.com",
            "logo_url": "https://logo.clearbit.com/karnsfoods.com",
            "address": "Varies by location"
        },
        {
            "name": "H-E-B",
            "website": "https://www.heb.com",
            "logo_url": "https://logo.clearbit.com/heb.com",
            "address": "Varies by location"
        },
        {
            "name": "ShopRite",
            "website": "https://www.shoprite.com",
            "logo_url": "https://logo.clearbit.com/shoprite.com",
            "address": "Varies by location"
        },
        {
            "name": "Winn-Dixie",
            "website": "https://www.winndixie.com",
            "logo_url": "https://logo.clearbit.com/winndixie.com",
            "address": "Varies by location"
        },
        {
            "name": "Stop & Shop",
            "website": "https://www.stopandshop.com",
            "logo_url": "https://logo.clearbit.com/stopandshop.com",
            "address": "Varies by location"
        },
        {
            "name": "Harris Teeter",
            "website": "https://www.harristeeter.com",
            "logo_url": "https://logo.clearbit.com/harristeeter.com",
            "address": "Varies by location"
        },
        {
            "name": "Hannaford",
            "website": "https://www.hannaford.com",
            "logo_url": "https://logo.clearbit.com/hannaford.com",
            "address": "Varies by location"
        },
        {
            "name": "Piggly Wiggly",
            "website": "https://www.pigglywiggly.com",
            "logo_url": "https://logo.clearbit.com/pigglywiggly.com",
            "address": "Varies by location"
        },
        {
            "name": "Save A Lot",
            "website": "https://www.savealot.com",
            "logo_url": "https://logo.clearbit.com/savealot.com",
            "address": "Varies by location"
        },
        {
            "name": "Vons",
            "website": "https://www.vons.com",
            "logo_url": "https://logo.clearbit.com/vons.com",
            "address": "Varies by location"
        },
        {
            "name": "Acme Markets",
            "website": "https://www.acmemarkets.com",
            "logo_url": "https://logo.clearbit.com/acmemarkets.com",
            "address": "Varies by location"
        },
        {
            "name": "WinCo Foods",
            "website": "https://www.wincofoods.com",
            "logo_url": "https://logo.clearbit.com/wincofoods.com",
            "address": "Varies by location"
        },
        {
            "name": "Ralphs",
            "website": "https://www.ralphs.com",
            "logo_url": "https://logo.clearbit.com/ralphs.com",
            "address": "Varies by location"
        },
        {
            "name": "Lidl",
            "website": "https://www.lidl.com",
            "logo_url": "https://logo.clearbit.com/lidl.com",
            "address": "Varies by location"
        },
        {
            "name": "BJ's Wholesale",
            "website": "https://www.bjs.com",
            "logo_url": "https://logo.clearbit.com/bjs.com",
            "address": "Varies by location"
        },
        {
            "name": "Market Basket",
            "website": "https://www.shopmarketbasket.com",
            "logo_url": "https://logo.clearbit.com/shopmarketbasket.com",
            "address": "Varies by location"
        },
        {
            "name": "Price Chopper",
            "website": "https://www.pricechopper.com",
            "logo_url": "https://logo.clearbit.com/pricechopper.com",
            "address": "Varies by location"
        }
    ]

def search_store_info(query):
    """
    Search for store information based on the name.
    Uses Clearbit for logos and could be extended with other APIs for addresses.
    """
    # Normalize query
    query = query.strip().lower()

    # Check in common stores list first
    common_stores = get_common_store_data()
    for store in common_stores:
        if query in store["name"].lower():
            return store

    # If not found, try to get a logo from Clearbit
    try:
        website = f"https://www.{query.replace(' ', '')}.com"
        logo_url = f"https://logo.clearbit.com/{query.replace(' ', '')}.com"

        # Test if the logo exists
        urllib.request.urlopen(logo_url)

        return {
            "name": query.title(),
            "website": website,
            "logo_url": logo_url,
            "address": ""
        }
    except:
        # Return basic info if no logo found
        return {
            "name": query.title(),
            "website": "",
            "logo_url": "",
            "address": ""
        }

def find_matching_store_location(item, store):
    """
    Find the appropriate store location for an item based on its category.
    
    Args:
        item: GroceryItem object
        store: GroceryStore object
        
    Returns:
        StoreLocation object or None if no matching location found
    """
    from .models import ProductCategory
    
    # If item has no category, return None
    if not item.category:
        return None
        
    # Get a list of all store locations
    store_locations = StoreLocation.objects.filter(store=store)
    if not store_locations.exists():
        return None
        
    # Get item category name
    category_name = item.category.name
    
    # Map of category names to common store section names
    category_to_location_map = {
        # Produce-related
        'Vegetables': ['Produce', 'Fruits & Vegetables', 'Fresh Produce'],
        'Fruits': ['Produce', 'Fruits & Vegetables', 'Fresh Produce'],
        
        # Dairy-related
        'Dairy': ['Dairy', 'Refrigerated'],
        
        # Meat & Seafood
        'Meat': ['Meat', 'Meat & Seafood'],
        'Seafood': ['Seafood', 'Fish', 'Meat & Seafood'],
        
        # Bakery-related
        'Bakery': ['Bakery', 'Bread', 'Baked Goods'],
        
        # Pantry-related
        'Pantry': ['Dry Goods', 'Canned Goods', 'Pasta & Rice'],
        
        # Snacks-related
        'Snacks': ['Snacks', 'Chips & Crackers'],
        
        # Beverages-related
        'Beverages': ['Beverages', 'Drinks', 'Soda & Water'],
        
        # Frozen-related
        'Frozen': ['Frozen Foods', 'Frozen'],
        
        # Household-related
        'Household': ['Household', 'Cleaning Supplies', 'Home'],
        
        # Personal Care-related
        'Personal Care': ['Health & Beauty', 'Personal Care', 'Pharmacy'],
        
        # Baby & Pet-related
        'Baby & Pet': ['Baby Products', 'Pet Supplies', 'Pet Food']
    }
    
    # Find the matching location names for this category
    potential_location_names = category_to_location_map.get(category_name, [])
    
    # Add the category name itself as a potential match
    potential_location_names.append(category_name)
    
    # Try to find a matching location in the store
    for location_name in potential_location_names:
        for store_location in store_locations:
            if location_name.lower() in store_location.name.lower():
                return store_location
    
    # If no match found, return None
    return None

def save_store_logo_from_url(store, logo_url):
    """
    Downloads a logo from a URL and saves it to the store object.

    Args:
        store: GroceryStore object to save the logo to
        logo_url: URL of the logo to download

    Returns:
        bool: True if successful, False otherwise
    """
    if not logo_url:
        return False

    try:
        # Create a proper request with user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        req = urllib.request.Request(logo_url, headers=headers)

        # Download the image
        with urllib.request.urlopen(req, timeout=10) as response:
            logo_data = response.read()
            content_type = response.headers.get('Content-Type', '').lower()

        # Check if we got valid image data
        if len(logo_data) < 100:  # Too small to be a valid image
            print(f"Downloaded data too small for {logo_url}")
            return False

        # Check content type for basic image validation
        valid_image_types = ['image/jpeg', 'image/png', 'image/gif', 'image/svg+xml', 'image/webp']
        if not any(image_type in content_type for image_type in valid_image_types):
            print(f"Content type '{content_type}' does not appear to be an image for {logo_url}")
            
            # Additional validation: Check for image signatures
            # JPEG starts with FF D8
            # PNG starts with 89 50 4E 47
            # GIF starts with 47 49 46 38
            is_jpeg = logo_data[:2] == b'\xff\xd8'
            is_png = logo_data[:4] == b'\x89PNG'
            is_gif = logo_data[:4] == b'GIF8'
            
            if not (is_jpeg or is_png or is_gif):
                return False
            # If we detected a valid image signature, continue despite the content type

        # Create safe filename
        safe_name = store.name.lower().replace(' ', '_').replace("'", "")
        
        # Determine extension based on content type or default to png
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = 'jpg'
        elif 'png' in content_type:
            ext = 'png'
        elif 'gif' in content_type:
            ext = 'gif'
        elif 'svg' in content_type:
            ext = 'svg'
        elif 'webp' in content_type:
            ext = 'webp'
        else:
            ext = 'png'  # Default to png
            
        filename = f"{store.id}_{safe_name}_logo.{ext}"

        # Save the image directly
        import tempfile
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(logo_data)
            temp_file_path = temp_file.name

        # Save the image
        with open(temp_file_path, 'rb') as temp_file:
            store.logo.save(filename, ContentFile(temp_file.read()), save=True)

        # Clean up temporary file
        os.unlink(temp_file_path)

        return True
    except Exception as e:
        import traceback
        print(f"Error saving logo: {str(e)}")
        print(traceback.format_exc())
        return False