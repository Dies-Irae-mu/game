from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from evennia.objects.models import ObjectDB
from evennia.utils.utils import inherits_from
from world.wod20th.models import CharacterSheet, CharacterImage
from django.core.paginator import Paginator
from evennia.utils.search import search_channel
from evennia.help.models import HelpEntry
from evennia.help.filehelp import FILE_HELP_ENTRIES
from evennia.commands.default.help import CmdHelp
from evennia.utils.utils import class_from_module
from django.conf import settings
from collections import defaultdict
from evennia.comms.models import ChannelDB
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import uuid
from markdown2 import Markdown

markdowner = Markdown(extras=['fenced-code-blocks', 'tables', 'break-on-newline'])

@login_required
def sheet(request, key, dbref):
    """View for displaying character sheets."""
    try:
        # Get the character object directly
        character = ObjectDB.objects.get(id=dbref)
        if not character:
            raise Http404("Character not found.")
        
        # More explicit permission checks
        can_edit = False
        account = request.user
        
        # Check if user is staff or has edit permissions
        if account.is_staff or character.account == account or character in account.db._playable_characters:
            can_edit = True
        
        # Get character stats (if they exist)
        stats = character.db.stats or {}
        
        # Define vitals fields
        vitals_fields = [
            {'id': 'full_name', 'label': 'Full Name', 'value': character.db.full_name or ''},
            {'id': 'appears_as', 'label': 'Appears As', 'value': character.db.appears_as or ''},
            {'id': 'apparent_age', 'label': 'Apparent Age', 'value': character.db.apparent_age or ''},
            {'id': 'date_of_birth', 'label': 'Date of Birth', 'value': character.db.date_of_birth or ''},
            {'id': 'demeanor', 'label': 'Demeanor', 'value': character.db.demeanor or ''},
            {'id': 'occupation', 'label': 'Occupation', 'value': character.db.occupation or ''},
            {'id': 'affiliation', 'label': 'Affiliation', 'value': character.db.affiliation or ''}
        ]
        
        # Get character images
        character_images = CharacterImage.objects.filter(character=character).order_by('-is_primary', '-id')[:5]
        
        # Check character permissions and status
        is_staff = False
        is_storyteller = False
        staff_permissions = ["developer", "admin", "builder"]
        
        # Get all permission tags for the character
        permission_tags = [tag.db_key for tag in character.db_tags.filter(db_tagtype="permission")]
        
        # Check for staff permissions in character's permission tags
        if any(perm in permission_tags for perm in staff_permissions):
            is_staff = True
        # Check for storyteller tag
        elif "storyteller" in permission_tags:
            is_storyteller = True
        # Fallback to account checks if not found in character permissions
        elif character.account and (character.account.is_staff or character.account.is_superuser):
            is_staff = True
            
        # A character is considered approved if:
        # 1. They have the approved tag OR
        # 2. They are staff (is_staff) OR
        # 3. They are a storyteller
        is_approved = character.db.approved or is_staff or is_storyteller
        
        # Convert markdown text fields
        biography_html = markdowner.convert(character.db.biography or "")
        rp_hooks_html = markdowner.convert(character.db.rp_hooks or "")
        notable_stats_html = markdowner.convert(character.db.notable_stats or "")
        soundtrack_html = markdowner.convert(character.db.soundtrack or "")
        
        # Format the context
        context = {
            'character': character,
            'splat': stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', 'Mortal'),
            'approved': is_approved,  # Use our new approval logic
            'can_edit': can_edit,
            'biography': character.db.biography or "",
            'biography_html': biography_html,
            'rp_hooks': character.db.rp_hooks or "",
            'rp_hooks_html': rp_hooks_html,
            'image_url': character.db.image_url or "",
            'vitals_fields': vitals_fields,
            'notable_stats': character.db.notable_stats or "",
            'notable_stats_html': notable_stats_html,
            'soundtrack': character.db.soundtrack or "",
            'soundtrack_html': soundtrack_html,
            'character_images': character_images,
            'is_staff': is_staff,  # Pass staff status to template
            'is_storyteller': is_storyteller  # Pass storyteller status to template
        }

        return render(request, 'website/character/sheet.html', context)

    except ObjectDB.DoesNotExist:
        raise Http404("Character not found.")
    except ValueError as e:
        raise Http404(str(e))

@login_required
@require_POST
def update_character_field(request, key, dbref):
    """Update a character's editable field."""
    try:
        character = ObjectDB.objects.get(id=dbref)
        if not character.access(request.user, 'edit') and not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        field = request.POST.get('field')
        value = request.POST.get('value')

        # List of allowed fields
        allowed_fields = [
            'biography', 'rp_hooks', 'image_url', 'notable_stats', 'soundtrack',
            'full_name', 'appears_as', 'apparent_age', 'date_of_birth',
            'demeanor', 'occupation', 'affiliation'
        ]

        if field in allowed_fields:
            setattr(character.db, field, value)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Invalid field'}, status=400)

    except ObjectDB.DoesNotExist:
        return JsonResponse({'error': 'Character not found'}, status=404)

def format_attributes(stats):
    """Helper function to format attributes for display."""
    attributes = {
        'Physical': ['Strength', 'Dexterity', 'Stamina'],
        'Social': ['Charisma', 'Manipulation', 'Appearance'],
        'Mental': ['Perception', 'Intelligence', 'Wits']
    }

    formatted = {}
    for category, attr_list in attributes.items():
        formatted[category] = []
        for attr in attr_list:
            value = stats.get('attributes', {}).get(category.lower(), {}).get(attr, 0)
            temp_value = stats.get('attributes', {}).get(category.lower(), {}).get(f"{attr}_temp", value)
            formatted[category].append({
                'name': attr,
                'value': value,
                'temp_value': temp_value
            })
    return formatted 

@login_required
def character_list(request):
    """View for displaying list of characters."""
    characters = ObjectDB.objects.filter(db_typeclass_path__contains='character').exclude(db_typeclass_path__contains='npc').order_by('db_key')
    
    # Set up pagination
    paginator = Paginator(characters, 20)  # Show 20 characters per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate half count for two-column layout based on current page
    current_page_count = len(page_obj.object_list)
    half_count = (current_page_count + 1) // 2  # Using ceiling division to handle odd numbers
    
    context = {
        'characters': page_obj.object_list,
        'half_count': half_count,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj
    }
    return render(request, 'website/character/list.html', context)

@login_required
def channel_list(request):
    """View for listing all channels."""
    channels = ChannelDB.objects.all()
    return render(request, 'website/channels/list.html', {'channels': channels})

@login_required
def channel_detail(request, channel_name):
    """View for displaying a specific channel's details and history."""
    channel = get_object_or_404(ChannelDB, db_key=channel_name)
    messages = channel.db.messages[-20:] if channel.db.messages else []  # Get last 20 messages
    return render(request, 'website/channels/detail.html', {
        'channel': channel,
        'messages': messages
    })

def help_index(request):
    """View for the help system index."""
    # Get all help entries from different sources
    db_help_entries = HelpEntry.objects.all().order_by('db_key')
    file_help_entries = FILE_HELP_ENTRIES.all()
    
    # Initialize command help with proper cmdsets
    cmd_help = CmdHelp()
    cmd_help.caller = request.user
    
    # Create and populate the command sets
    from commands.default_cmdsets import CharacterCmdSet, AccountCmdSet
    char_cmdset = CharacterCmdSet()
    char_cmdset.at_cmdset_creation()
    account_cmdset = AccountCmdSet()
    account_cmdset.at_cmdset_creation()
    
    # Merge the cmdsets
    char_cmdset.add(account_cmdset)
    cmd_help.cmdset = char_cmdset
    
    # Get all help entries
    cmd_help_topics, db_help_topics, file_help_topics = cmd_help.collect_topics(request.user, mode="list")
    
    categories = defaultdict(list)
    
    # Process command help entries
    for key, cmd in cmd_help_topics.items():
        category = cmd.help_category or 'General'
        help_text = cmd.get_help(request.user, char_cmdset) or ''
        
        # Clean up the key for display
        display_name = key.strip().replace('_', ' ')
        if display_name.startswith('+'):
            display_name = display_name[1:]
        elif display_name.startswith('@'):
            display_name = display_name[1:]
            
        categories[category].append({
            'key': key,
            'name': display_name,
            'summary': help_text[:200] + '...' if len(help_text) > 200 else help_text,
            'category': category,
            'type': 'command'
        })
    
    # Process database help entries
    for entry in db_help_entries:
        category = entry.help_category or 'General'
        help_text = entry.entrytext or ''
        
        # Clean up the key for display
        display_name = entry.key.strip().replace('_', ' ')
        if display_name.startswith('+'):
            display_name = display_name[1:]
        elif display_name.startswith('@'):
            display_name = display_name[1:]
            
        categories[category].append({
            'key': entry.key,
            'name': display_name,
            'summary': help_text[:200] + '...' if len(help_text) > 200 else help_text,
            'category': category,
            'type': 'database'
        })
    
    # Process file-based help entries
    for entry in file_help_entries:
        category = entry.help_category or 'General'
        help_text = entry.entrytext or ''
        
        # Clean up the key for display
        display_name = entry.key.strip().replace('_', ' ')
        if display_name.startswith('+'):
            display_name = display_name[1:]
        elif display_name.startswith('@'):
            display_name = display_name[1:]
            
        categories[category].append({
            'key': entry.key,
            'name': display_name,
            'summary': help_text[:200] + '...' if len(help_text) > 200 else help_text,
            'category': category,
            'type': 'file'
        })
    
    # Sort categories and their topics
    formatted_categories = []
    for category, topics in sorted(categories.items()):
        # Sort topics by name, ignoring case and special characters
        sorted_topics = sorted(topics, key=lambda x: x['name'].lower().lstrip('+-@'))
        formatted_categories.append({
            'name': category,
            'topics': sorted_topics
        })
    
    return render(request, 'website/help/index.html', {
        'categories': formatted_categories,
        'active_category': request.GET.get('category', '')
    })

def help_category(request, category):
    """View for displaying all help entries in a category."""
    help_entries = HelpEntry.objects.filter(help_category=category)
    return render(request, 'website/help/category.html', {
        'category': category,
        'entries': help_entries
    })

def help_topic(request, category, topic):
    """View for displaying a specific help entry."""
    # Initialize command help with proper cmdsets
    cmd_help = CmdHelp()
    cmd_help.caller = request.user
    
    # Create and populate the command sets
    from commands.default_cmdsets import CharacterCmdSet, AccountCmdSet
    char_cmdset = CharacterCmdSet()
    char_cmdset.at_cmdset_creation()
    account_cmdset = AccountCmdSet()
    account_cmdset.at_cmdset_creation()
    
    # Merge the cmdsets
    char_cmdset.add(account_cmdset)
    cmd_help.cmdset = char_cmdset
    
    # Get all help entries
    cmd_help_topics, db_help_topics, file_help_topics = cmd_help.collect_topics(request.user, mode="list")
    
    # Try to find the help entry in different sources
    entry = None
    help_text = None
    
    # First check database entries
    try:
        entry = HelpEntry.objects.get(db_help_category=category, db_key=topic)
        help_text = entry.db_entrytext
    except HelpEntry.DoesNotExist:
        # Then check command help entries
        if topic in cmd_help_topics:
            cmd = cmd_help_topics[topic]
            if cmd.help_category.lower() == category.lower():
                help_text = cmd.get_help(request.user, char_cmdset)
                entry = type('CommandHelp', (), {
                    'db_key': topic,
                    'db_help_category': category,
                    'db_entrytext': help_text
                })()
        # Finally check file-based help entries
        if not entry:
            for file_entry in FILE_HELP_ENTRIES.all():
                if file_entry.key == topic and file_entry.help_category.lower() == category.lower():
                    help_text = file_entry.entrytext
                    entry = type('FileHelp', (), {
                        'db_key': topic,
                        'db_help_category': category,
                        'db_entrytext': help_text
                    })()
                    break
    
    if not entry:
        raise Http404("Help entry not found")
    
    # Get next and previous topics in the same category
    all_topics = []
    for key, cmd in cmd_help_topics.items():
        if cmd.help_category.lower() == category.lower():
            all_topics.append(key)
    
    # Add database topics
    db_entries = HelpEntry.objects.filter(db_help_category=category).values_list('db_key', flat=True)
    all_topics.extend(db_entries)
    
    # Add file-based topics
    for file_entry in FILE_HELP_ENTRIES.all():
        if file_entry.help_category.lower() == category.lower():
            all_topics.append(file_entry.key)
    
    # Sort all topics
    all_topics = sorted(set(all_topics))
    current_index = all_topics.index(topic)
    
    next_topic = all_topics[current_index + 1] if current_index < len(all_topics) - 1 else None
    prev_topic = all_topics[current_index - 1] if current_index > 0 else None
    
    # Get related topics (same category)
    related_topics = [t for t in all_topics if t != topic][:5]
    
    return render(request, 'website/help/topic.html', {
        'entry': entry,
        'category': category,
        'next_topic': next_topic,
        'prev_topic': prev_topic,
        'related_topics': related_topics,
        'help_text': help_text
    })

@login_required
@require_POST
def upload_character_image(request, key, dbref):
    """Handle character image upload."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)

    character = get_object_or_404(ObjectDB, db_key=key, id=dbref)
    if not (request.user.is_staff or character.access(request.user, 'edit')):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    if 'image' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No image file provided'}, status=400)

    image_file = request.FILES['image']
    if not image_file.content_type.startswith('image/'):
        return JsonResponse({'success': False, 'error': 'Invalid file type'}, status=400)

    if image_file.size > 5 * 1024 * 1024:  # 5MB limit
        return JsonResponse({'success': False, 'error': 'File too large'}, status=400)

    # Generate unique filename
    ext = os.path.splitext(image_file.name)[1].lower()
    filename = f"{uuid.uuid4()}{ext}"
    
    # Create directory path
    filepath = f"characters/{character.id}/{filename}"
    full_path = os.path.join(settings.MEDIA_ROOT, 'characters', str(character.id))
    os.makedirs(full_path, exist_ok=True)

    try:
        # Create a new image record
        image = CharacterImage(character=character)
        
        # If this is the first image, make it primary
        if not CharacterImage.objects.filter(character=character).exists():
            image.is_primary = True

        # Save the new image file
        with default_storage.open(filepath, 'wb+') as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)

        image.image = filepath
        image.save()

        return JsonResponse({'success': True, 'image_url': image.image.url})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def set_primary_image(request, key, dbref, image_id):
    """Set an image as the primary image for a character."""
    character = get_object_or_404(ObjectDB, db_key=key, id=dbref)
    if not (request.user.is_staff or character.access(request.user, 'edit')):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    try:
        # Get the image to make primary
        image = get_object_or_404(CharacterImage, id=image_id, character=character)
        
        # Set all other images to non-primary
        CharacterImage.objects.filter(character=character).update(is_primary=False)
        
        # Set this image as primary
        image.is_primary = True
        image.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def delete_character_image(request, key, dbref, image_id):
    """Delete a character image."""
    character = get_object_or_404(ObjectDB, db_key=key, id=dbref)
    if not (request.user.is_staff or character.access(request.user, 'edit')):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    try:
        # Get the image to delete
        image = get_object_or_404(CharacterImage, id=image_id, character=character)
        was_primary = image.is_primary
        
        # Delete the image file and record
        if image.image:
            image.image.delete()
        image.delete()
        
        # If this was the primary image, set a new primary
        if was_primary:
            next_image = CharacterImage.objects.filter(character=character).order_by('-id').first()
            if next_image:
                next_image.is_primary = True
                next_image.save()
        
        return JsonResponse({
            'success': True,
            'new_primary_id': next_image.id if was_primary and next_image else None
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

