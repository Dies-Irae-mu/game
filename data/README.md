# Data Dictionary

This folder contains all of the data files to establish a World of Darkness 20th Anniversary game.

## Core Features

- **JSON Data Storage**: Structured data files for game mechanics and entities
- **Reference Information**: Rules data used by various game systems
- **Character Options**: Powers, abilities, and traits for character creation and advancement
- **Initialization Data**: Base values used to populate the database during setup

## Type Data
Due to Vampire being the first-created game line for Dies Irae, the vampire files contain much of the basic data that applies to all spheres (vampire_bio, vampire_abilities, etc.).

- **Bio** files are the "topmatter" part of the character sheet. This is usually specific to the splat (Dies Irae name for 'sphere' or game line), like Mages will have 'Affiliation' which is linked to Traditions, Technocracy, Nephandi, or none, which then opens up other bio stats like Tradition, Convention, Nephandi Faction. 
- **Backgrounds** files contain the splat-specific backgrounds (Pure Breed, Fetish, Ancestors for Shifter, etc.)
- **Merits** files contain merits that are found in the splat's book material. They may not be specific to the individual splat, for instance many of the Mage merits can be used by anyone.
- **Flaws** files contain flaws that are found in the splat's book material. They may not be specific to the individual splat, for instance many of the Mage flaws can be used by anyone.
- **Pools** files contain anything that might be used to fuel the character or serve as a kind of advantage to the character that's either spent/regained, or acts as an indicator of supernatural strength (Gnosis, Willpower, Renown, Arete, Glamour, Blood, etc.)

### Shifter
- shifter_bio.json
- shifter_pools.json
- shifter_backgrounds.json
- garou_merits.json
- garou_flaws.json
- fera_merits.json
- fera_flaws.json

Gift files exist for Garou (Werewolf):
- rank1_garou_gifts.json
- rank2_garou_gifts.json
- rank3_garou_gifts.json
- rank4_garou_gifts.json
- rank5_garou_gifts.json
- rank6_garou_gifts.json
- hakken_gifts.json

Gift files also exist for other Shifters (Fera or Changing Breeds):
- ajaba_gifts.json
- ananasi_gifts.json
- bastet_gifts.json
- corax_gifts.json
- gurahl_gifts.json
- kitsune_gifts.json
- mokole_gifts.json
- nagah_gifts.json
- nuwisha_gifts.json
- ratkin_gifts.json
- rokea_gifts.json

Rites files also exist:
- fera_bsd_rites.json
- garou_rites.json

Gifts related to Wyrm-based shifters (Fallen Fera or Black Spiral Dancers) exist in:
- wyrm_gifts.json

### Vampire
- vampire_bio.json
- vampire_abilities.json -- this contains all of the basic abilities in the character sheet (attributes, abilities, secondary abilities, etc.)
- vampire_disciplines.json
- vampire_pools.json
- vampire_merits.json
- vampire_flaws.json
- necromancy_rituals.json
- thaum_rituals.json
- combo_disciplines.json
- combo_disciplines2.json

### Mage
- mage_bio.json
- mage_spheres.json
- mage_merits.json
- mage_flaws.json
- mage_pools.json
- mage_backgrounds.json

### Companions/Bygones
- companion_flaws.json
- companion_merits.json
- special_advantages.json

### Changeling
- changeling_bio.json
- changeling_backgrounds.json
- changeling_arts_realms.json
- changeling_merits.json
- changeling_flaws.json
- changeling_pools.json

### Mortal+ (minor template characters and fomori/kami)
- mortalplus_backgrounds.json
- mortalplus_bio.json
- mortalplus_flaws.json
- mortalplus_merits.json
- mortalplus_powers.json -- includes sorcery, numina, and faith powers which are specific to Dies Irae.
- sorcerer_rituals.json
- possessed_bio.json
- possessed_blessings.json
- possessed_flaws.json
- possessed_merits.json

### Wraith
- wraith_backgrounds.json
- wraith_bio.json
- wraith_powers.json

### Common
- attributes_basic_backgrounds.json
- charms.json
- virtues.json
- splat_abilities.json -- this contains the specific abilities for different splats, like Primal-Urge for Shifters, or a mishmash of secondary abilities for Mages.

## Data Structure

Each JSON file follows a consistent structure for the data type it represents. For example, gift files typically include:

```json
[
  {
    "name": "Gift Name",
    "rank": 1,
    "description": "Description of what the gift does",
    "system": "Rules mechanics for how the gift functions",
    "source": "Source book reference",
    "splat": "Shifter",
    "tribe": ["Tribe1", "Tribe2", "Ananasi uses Aspect for this"],
    "breed": "Breed requirement (if any)",
    "auspice": "Auspice requirement (if any); Non-Ananasi use Aspect for this; Ananasi use 'Ananasi Faction' to represent auspice.",
    "gift_alias": "Alias that might exist for another Shifter breed",
    "game_line": "Werewolf: The Apocalypse",
    "category": "powers",
    "stat_type": "gift",
    "values": [1, 2, 3, 4, 5],
  }
]
```

## Integration

The data files are used by:
- The wod20th Django app for character creation and management
- Character advancement and XP systems
- Command systems for activating powers and abilities
- Staff tools for reference and game management

## Usage

Data in these files is loaded into the database using the `load_wod20th_stats` management command. This should be run during initial setup and whenever data files are updated:

```
python manage.py load_wod20th_stats
```

Individual data files can be specified to reload only certain types of data:

```
python manage.py load_wod20th_stats --file=rank1_garou_gifts.json
```

See world/wod20th/README.md for more information.

## Development

When adding new data files:

1. Follow the established JSON structure for the relevant data type
2. Ensure all required fields are present
3. Run validation tests before deployment
4. Update this README to include any new data file categories

When modifying existing data:

1. Back up the current file before making changes
2. Test changes thoroughly before deploying to production
3. Consider database migration needs if changing data structure