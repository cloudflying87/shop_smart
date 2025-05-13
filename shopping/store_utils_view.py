from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.management import call_command
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from shopping.models import GroceryStore, Family, StoreLocation
from shopping.store_utils import get_common_store_data
import io
import sys
import logging

logger = logging.getLogger(__name__)

@login_required
@require_POST
def delete_all_stores(request):
    """Delete all stores and their locations"""
    try:
        # Count stores before deletion
        store_count = GroceryStore.objects.count()
        location_count = StoreLocation.objects.count()

        # Delete all store locations first (handles foreign key constraints)
        StoreLocation.objects.all().delete()

        # Delete all stores
        GroceryStore.objects.all().delete()

        # Log the action
        logger.info(f"User {request.user.username} deleted all stores ({store_count} stores, {location_count} locations)")

        # Send success message
        messages.success(
            request,
            f"Successfully deleted {store_count} stores and {location_count} store locations."
        )
    except Exception as e:
        logger.exception("Error deleting all stores")
        messages.error(request, f"An error occurred: {str(e)}")

    return redirect('groceries:stores')

@login_required
@require_POST
def delete_store(request, pk):
    """Delete a specific store and its locations"""
    try:
        # Get the store
        store = GroceryStore.objects.get(pk=pk)
        store_name = store.name

        # Count locations before deletion
        location_count = StoreLocation.objects.filter(store=store).count()

        # Delete locations first (handles foreign key constraints)
        StoreLocation.objects.filter(store=store).delete()

        # Delete the store
        store.delete()

        # Log the action
        logger.info(f"User {request.user.username} deleted store {store_name} (pk={pk}) with {location_count} locations")

        # Send success message
        messages.success(
            request,
            f"Successfully deleted '{store_name}' and {location_count} store locations."
        )
    except GroceryStore.DoesNotExist:
        messages.error(request, "Store not found.")
    except Exception as e:
        logger.exception(f"Error deleting store with id {pk}")
        messages.error(request, f"An error occurred: {str(e)}")

    return redirect('groceries:stores')

@method_decorator(login_required, name='dispatch')
class StorePopulationView(View):
    """View for populating stores from the UI"""
    
    def get(self, request):
        """Display the store population form"""
        # Get available stores
        available_stores = get_common_store_data()
        
        # Get current stores in the database
        existing_stores = GroceryStore.objects.all()
        existing_store_names = [store.name.lower() for store in existing_stores]
        
        # Separate stores into existing and new
        stores_data = []
        for store in available_stores:
            is_existing = store['name'].lower() in existing_store_names
            stores_data.append({
                'name': store['name'],
                'website': store.get('website', ''),
                'logo_url': store.get('logo_url', ''),
                'is_existing': is_existing
            })
        
        # Get user's families
        families = Family.objects.filter(members__user=request.user)
        
        context = {
            'stores': stores_data,
            'families': families,
            'existing_count': len(existing_store_names),
            'available_count': len(available_stores)
        }
        return render(request, 'groceries/stores/populate.html', context)
    
    def post(self, request):
        """Handle the store population form submission"""
        selected_stores = request.POST.getlist('selected_stores')
        family_id = request.POST.get('family')
        skip_logos = request.POST.get('skip_logos') == 'on'
        clear_existing = request.POST.get('clear_existing') == 'on'
        
        if not selected_stores:
            messages.warning(request, "No stores were selected")
            return redirect('groceries:populate_stores')
            
        # Capture management command output
        stdout_backup = sys.stdout
        stderr_backup = sys.stderr
        output_buffer = io.StringIO()
        sys.stdout = output_buffer
        sys.stderr = output_buffer
        
        try:
            # Prepare command arguments
            options = {
                'stores': selected_stores,
                'nologos': skip_logos,
                'clear': clear_existing
            }

            if family_id:
                options['family'] = int(family_id)

            # Make sure we're downloading all assets
            # This ensures logos are downloaded and locations are created
            # Note: Locations are created by default in the populate_stores command

            # Run the management command
            call_command('populate_stores', **options)
            
            # Process output
            output = output_buffer.getvalue()
            stores_created = output.count("Created store:")
            
            # Set appropriate message
            if stores_created > 0:
                messages.success(request, f"Successfully added {stores_created} new stores.")
            else:
                messages.info(request, "No new stores were added. They may already exist in the database.")
                
            return redirect('groceries:stores')
            
        except Exception as e:
            logger.exception("Error in populate_stores view")
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('groceries:populate_stores')
        finally:
            # Restore stdout/stderr
            sys.stdout = stdout_backup
            sys.stderr = stderr_backup