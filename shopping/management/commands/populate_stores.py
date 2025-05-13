import os
import urllib.request
import logging
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import transaction
from django.core.files.temp import NamedTemporaryFile
from shopping.models import GroceryStore, Family
from shopping.store_utils import get_common_store_data, create_default_store_locations, save_store_logo_from_url


logger = logging.getLogger(__name__)


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
        parser.add_argument(
            '--stores',
            type=str,
            nargs='+',
            help='Specific stores to import (e.g. "Walmart" "Target")'
        )
        parser.add_argument(
            '--nologos',
            action='store_true',
            help='Skip downloading store logos',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List available stores without adding them',
        )

    def handle(self, *args, **options):
        # Get common store data
        common_stores = get_common_store_data()

        # Just list available stores if requested
        if options['list']:
            self.stdout.write(self.style.SUCCESS("Available stores:"))
            for store in common_stores:
                self.stdout.write(f"- {store['name']}")
            return

        # Clear existing stores if requested
        if options['clear']:
            self.stdout.write('Clearing existing stores...')
            GroceryStore.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('All stores removed!'))

        # Filter stores if specific ones are requested
        if options['stores']:
            specified_stores = [s.lower() for s in options['stores']]
            common_stores = [s for s in common_stores if s['name'].lower() in specified_stores]
            if not common_stores:
                self.stdout.write(self.style.WARNING(f"No matching stores found. Use --list to see available stores."))
                return
            self.stdout.write(f"Importing {len(common_stores)} specified stores")

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

        # If no families, create one default family
        if not families.exists():
            self.stdout.write(self.style.WARNING('No families found. Creating a default family.'))
            default_family = Family.objects.create(name="Default Family")
            families = [default_family]
            self.stdout.write(self.style.SUCCESS(f'Created default family with ID: {default_family.id}'))

        # Create stores
        stores_created = 0
        stores_updated = 0
        locations_created = 0
        logos_downloaded = 0

        for store_data in common_stores:
            name = store_data['name']
            slug = slugify(name)

            try:
                with transaction.atomic():
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
                        self.stdout.write(self.style.SUCCESS(f'Created store: {name}'))

                        # Create default store locations
                        locations = create_default_store_locations(store)
                        locations_created += len(locations)
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
                    if not options['nologos'] and not store.logo and 'logo_url' in store_data and store_data['logo_url']:
                        self.stdout.write(f'  - Downloading logo from {store_data["logo_url"]}')
                        try:
                            if save_store_logo_from_url(store, store_data['logo_url']):
                                self.stdout.write(self.style.SUCCESS('  - Logo downloaded successfully'))
                                logos_downloaded += 1
                            else:
                                self.stdout.write(self.style.WARNING('  - Failed to download logo'))
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f'  - Error downloading logo: {str(e)}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating store {name}: {str(e)}"))
                logger.exception(f"Error in populate_stores for {name}")

        # Print summary
        self.stdout.write(self.style.SUCCESS(
            f'Done! Created {stores_created} new stores, updated {stores_updated} existing stores\n'
            f'Added {locations_created} total store locations, downloaded {logos_downloaded} logos'
        ))

        # Add helpful next steps
        if stores_created > 0:
            self.stdout.write("\nNext steps:")
            self.stdout.write("1. Go to http://localhost:8000/app/stores/ to view your stores")
            if options['family']:
                self.stdout.write(f"2. Visit your family profile to set a default store")
            else:
                self.stdout.write("2. Create a new shopping list using one of your new stores")