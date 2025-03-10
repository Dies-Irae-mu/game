from django.http import Http404
from django.shortcuts import render
from evennia.objects.models import ObjectDB
from evennia.utils.utils import inherits_from

def sheet(request, dbref):
    """View for displaying character sheets."""
    try:
        # Get character by dbref
        character = ObjectDB.objects.get(id=dbref)
    except ObjectDB.DoesNotExist:
        raise Http404("Character not found.")
    
    if not inherits_from(character, "typeclasses.characters.Character"):
        raise Http404("This object is not a character.")

    # Get character stats
    stats = character.db.stats
    if not stats:
        raise Http404("This character has no stats.")

    # Get basic info
    splat = stats.get('other', {}).get('splat', {}).get('Splat', {}).get('perm', 'Mortal')
    identity = stats.get('identity', {})
    lineage = identity.get('lineage', {})
    personal = identity.get('personal', {})

    # Format attributes
    attributes = {
        'Physical': ['Strength', 'Dexterity', 'Stamina'],
        'Social': ['Charisma', 'Manipulation', 'Appearance'],
        'Mental': ['Perception', 'Intelligence', 'Wits']
    }

    formatted_attributes = {}
    for category, attr_list in attributes.items():
        formatted_attributes[category] = []
        for attr in attr_list:
            value = character.get_stat('attributes', category.lower(), attr)
            temp_value = character.get_stat('attributes', category.lower(), attr, temp=True)
            formatted_attributes[category].append({
                'name': attr,
                'value': value if value is not None else 0,
                'temp_value': temp_value if temp_value is not None else value
            })

    context = {
        'character': character,
        'splat': splat,
        'identity': {
            'personal': personal,
            'lineage': lineage
        },
        'attributes': formatted_attributes,
        'abilities': stats.get('abilities', {}),
        'secondary_abilities': stats.get('secondary_abilities', {}),
        'backgrounds': stats.get('backgrounds', {}).get('background', {}),
        'merits': stats.get('merits', {}),
        'flaws': stats.get('flaws', {}),
        'virtues': stats.get('virtues', {}).get('moral', {}),
        'pools': stats.get('pools', {}).get('dual', {}),
        'approved': character.db.approved
    }

    return render(request, 'character/sheet.html', context) 
