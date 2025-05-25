from django.core.management.base import BaseCommand
from evennia.objects.models import ObjectDB
from evennia.utils import logger
from typeclasses.characters import Character

class Command(BaseCommand):
    """
    Django management command to fix gift aliases for all characters.
    
    This command ensures:
    1. All characters have a properly initialized gift_aliases attribute
    2. The gift_aliases attribute follows the correct format
    3. Any existing aliases are preserved and converted to the correct format
    """
    
    help = "Fix gift aliases for all characters in the database"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--dryrun",
            action="store_true",
            help="Perform a dry run without making changes",
        )
        parser.add_argument(
            "--character",
            type=str,
            help="Specify a character name to fix just that character",
        )
    
    def handle(self, *args, **options):
        """
        Main command handling function.
        """
        dryrun = options["dryrun"]
        single_char = options.get("character")
        
        self.stdout.write(f"Running in {'dry run' if dryrun else 'live'} mode")

        # Get all characters or a specific one
        if single_char:
            characters = ObjectDB.objects.filter(
                db_typeclass_path__contains="typeclasses.characters.Character",
                db_key__iexact=single_char
            )
            self.stdout.write(f"Targeting specific character: {single_char}")
        else:
            characters = ObjectDB.objects.filter(
                db_typeclass_path__contains="typeclasses.characters.Character"
            )
            self.stdout.write(f"Found {characters.count()} characters to process")

        fixed_count = 0
        skipped_count = 0
        error_count = 0

        for obj in characters:
            try:
                # Make sure it's a Character
                if not obj.is_typeclass("typeclasses.characters.Character"):
                    skipped_count += 1
                    continue

                # Check if character has gift_aliases attribute
                if not hasattr(obj.db, 'gift_aliases'):
                    if not dryrun:
                        # Initialize the gift_aliases attribute as an empty dict
                        obj.db.gift_aliases = {}
                        self.stdout.write(f"Initialized gift_aliases for {obj.name}")
                    else:
                        self.stdout.write(f"[DRY RUN] Would initialize gift_aliases for {obj.name}")
                    fixed_count += 1
                    continue
                
                # If gift_aliases is None, initialize it as an empty dict
                if obj.db.gift_aliases is None:
                    if not dryrun:
                        obj.db.gift_aliases = {}
                        self.stdout.write(f"Initialized gift_aliases for {obj.name} (was None)")
                    else:
                        self.stdout.write(f"[DRY RUN] Would initialize gift_aliases for {obj.name} (was None)")
                    fixed_count += 1
                    continue
                
                # Check each gift alias and fix format if needed
                fixed_entries = False
                
                # Create a copy of the gift_aliases dict to avoid modifying it during iteration
                aliases_to_process = dict(obj.db.gift_aliases)
                
                for canonical_name, alias_data in aliases_to_process.items():
                    # Skip if the canonical name is in an invalid format
                    if not isinstance(canonical_name, str):
                        continue
                        
                    # Convert old format to new format if needed
                    if isinstance(alias_data, str):
                        # Very old format: direct string
                        if not dryrun:
                            obj.db.gift_aliases[canonical_name] = {
                                'aliases': [alias_data],
                                'rating': 1  # Default rating
                            }
                            self.stdout.write(f"Converted old format (string) for {obj.name}: {canonical_name} -> {alias_data}")
                        else:
                            self.stdout.write(f"[DRY RUN] Would convert old format (string) for {obj.name}: {canonical_name} -> {alias_data}")
                        fixed_entries = True
                    elif isinstance(alias_data, dict):
                        # Check for old dict format with 'alias' key
                        if 'alias' in alias_data and 'aliases' not in alias_data:
                            alias = alias_data['alias']
                            rating = alias_data.get('rating', 1)
                            
                            if not dryrun:
                                obj.db.gift_aliases[canonical_name] = {
                                    'aliases': [alias] if isinstance(alias, str) else [str(alias)],
                                    'rating': rating
                                }
                                self.stdout.write(f"Converted old format (dict with 'alias') for {obj.name}: {canonical_name} -> {alias}")
                            else:
                                self.stdout.write(f"[DRY RUN] Would convert old format (dict with 'alias') for {obj.name}: {canonical_name} -> {alias}")
                            fixed_entries = True
                        elif 'aliases' in alias_data:
                            # New format but ensure aliases is a list
                            aliases = alias_data['aliases']
                            if not isinstance(aliases, list):
                                if not dryrun:
                                    obj.db.gift_aliases[canonical_name]['aliases'] = [str(aliases)]
                                    self.stdout.write(f"Fixed aliases format for {obj.name}: {canonical_name}")
                                else:
                                    self.stdout.write(f"[DRY RUN] Would fix aliases format for {obj.name}: {canonical_name}")
                                fixed_entries = True
                            
                            # Ensure rating exists
                            if 'rating' not in alias_data:
                                if not dryrun:
                                    obj.db.gift_aliases[canonical_name]['rating'] = 1
                                    self.stdout.write(f"Added missing rating for {obj.name}: {canonical_name}")
                                else:
                                    self.stdout.write(f"[DRY RUN] Would add missing rating for {obj.name}: {canonical_name}")
                                fixed_entries = True
                    
                    # Check for self-referential aliases (where the canonical name is its own alias)
                    if isinstance(alias_data, dict) and 'aliases' in alias_data:
                        aliases = alias_data['aliases']
                        if isinstance(aliases, list) and any(a.lower() == canonical_name.lower() for a in aliases if isinstance(a, str)):
                            # Remove the self-referential alias
                            if not dryrun:
                                obj.db.gift_aliases[canonical_name]['aliases'] = [
                                    a for a in aliases if isinstance(a, str) and a.lower() != canonical_name.lower()
                                ]
                                # If no aliases left, remove the entire entry
                                if not obj.db.gift_aliases[canonical_name]['aliases']:
                                    del obj.db.gift_aliases[canonical_name]
                                    self.stdout.write(f"Removed empty alias entry for {obj.name}: {canonical_name}")
                                else:
                                    self.stdout.write(f"Removed self-referential alias for {obj.name}: {canonical_name}")
                            else:
                                self.stdout.write(f"[DRY RUN] Would remove self-referential alias for {obj.name}: {canonical_name}")
                            fixed_entries = True

                if fixed_entries:
                    fixed_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                error_count += 1
                logger.log_err(f"Error processing character {obj.db_key}: {e}")
                continue

        self.stdout.write(self.style.SUCCESS(
            f"Complete: Fixed {fixed_count} characters, skipped {skipped_count} characters, encountered {error_count} errors."
        )) 