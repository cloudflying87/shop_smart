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

def save_store_logo_from_url(store, logo_url):
    """
    Downloads a logo from a URL and saves it to the store object.
    """
    if not logo_url:
        return

    try:
        # Download the image
        response = urllib.request.urlopen(logo_url)
        logo_data = response.read()

        # Extract filename from URL
        filename = f"{store.id}_{store.name.lower().replace(' ', '_')}_logo.png"

        # Save the image
        store.logo.save(filename, ContentFile(logo_data), save=True)
        return True
    except Exception as e:
        print(f"Error saving logo: {str(e)}")
        return False