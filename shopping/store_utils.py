from .models import GroceryStore, StoreLocation

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