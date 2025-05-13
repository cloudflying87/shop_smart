import os
import urllib.request
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from shopping.models import GroceryStore, Family
from shopping.store_utils import get_common_store_data, create_default_store_locations, save_store_logo_from_url


class Command(BaseCommand):
    help = 'Populates the database with common grocery stores'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing stores before adding new ones',
        )
        parser.add_argument(
            '--family',
            type=int,
            help='Family ID to associate stores with (default: all families)',
        )

    def handle(self, *args, **options):
        # Clear existing stores if requested
        if options['clear']:
            self.stdout.write('Clearing existing stores...')
            GroceryStore.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All stores removed!'))

        # Get common store data
        common_stores = get_common_store_data()
        
        # Get families
        if options['family']:
            try:
                families = [Family.objects.get(id=options['family'])]
                self.stdout.write(f'Using family: {families[0].name}')
            except Family.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Family with ID {options["family"]} not found!'))
                return
        else:
            families = Family.objects.all()
            self.stdout.write(f'Found {families.count()} families, associating stores with all of them')
        
        if not families.exists():
            self.stdout.write(self.style.ERROR('No families found! Create at least one family first.'))
            return

        # Create stores
        stores_created = 0
        stores_updated = 0
        for store_data in common_stores:
            name = store_data['name']
            slug = slugify(name)
            
            # Check if store already exists
            store, created = GroceryStore.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'address': store_data['address'],
                    'website': store_data['website'],
                }
            )
            
            if created:
                stores_created += 1
                self.stdout.write(f'Created store: {name}')
                
                # Create default store locations
                locations = create_default_store_locations(store)
                self.stdout.write(f'  - Added {len(locations)} store locations')
                
                # Associate with families
                store.families.add(*families)
                self.stdout.write(f'  - Associated with {families.count()} families')
            else:
                stores_updated += 1
                self.stdout.write(f'Store already exists: {name}, updating details')
                
                # Update store details
                store.address = store_data['address']
                store.website = store_data['website']
                store.save()
                
                # Ensure association with families
                for family in families:
                    if family not in store.families.all():
                        store.families.add(family)
                        self.stdout.write(f'  - Associated with family: {family.name}')
            
            # Download and save logo if not already set
            if not store.logo and 'logo_url' in store_data and store_data['logo_url']:
                self.stdout.write(f'  - Downloading logo from {store_data["logo_url"]}')
                if save_store_logo_from_url(store, store_data['logo_url']):
                    self.stdout.write(self.style.SUCCESS('  - Logo downloaded successfully'))
                else:
                    self.stdout.write(self.style.WARNING('  - Failed to download logo'))
        
        # Print summary
        self.stdout.write(self.style.SUCCESS(f'Done! Created {stores_created} new stores, updated {stores_updated} existing stores'))