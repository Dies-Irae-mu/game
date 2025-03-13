# world/characters/sheet_defaults.py

TALENTS = {
    "Alertness": 0,
    "Athletics": 0,
    "Awareness": 0,
    "Brawl": 0,
    "Empathy": 0,
    "Expression": 0,
    "Flight": 0,
    "Intimidation": 0,
    "Kenning": 0,
    "Leadership": 0,
    "Primal-Urge": 0,
    "Streetwise": 0,
    "Subterfuge": 0
}

SKILLS = {
    "Animal Ken": 0,
    "Crafts": 0,
    "Drive": 0,
    "Etiquette": 0,
    "Firearms": 0,
    "Larceny": 0,
    "Melee": 0,
    "Performance": 0,
    "Security": 0,
    "Stealth": 0,
    "Survival": 0,
    "Technology": 0
}

KNOWLEDGES = {
    "Academics": 0,
    "Bureaucracy": 0,
    "Computer": 0,
    "Cosmology": 0,
    "Enigmas": 0,
    "Finance": 0,
    "Gremayre": 0,
    "Investigation": 0,
    "Law": 0,
    "Medicine": 0,
    "Occult": 0,
    "Politics": 0,
    "Rituals": 0,
    "Science": 0
}

SECONDARY_TALENTS = {
    "Artistry": 0,
    "Blatancy": 0,
    "Carousing": 0,
    "Diplomacy": 0,
    "Do": 0,
    "Flying": 0,
    "Intrigue": 0,
    "High Ritual": 0,
    "Lucid Dreaming": 0,
    "Mimicry": 0,
    "Scrounging": 0,
    "Seduction": 0,
    "Style": 0
}

SECONDARY_SKILLS = {
    "Archery": 0,  
    "Biotech": 0,
    "Energy Weapons": 0,
    "Fortune-Telling": 0,
    "Fencing": 0,
    "Gambling": 0,
    "Helmsman": 0,
    "Jury-Rigging": 0,
    "Martial Arts": 0,
    "Microgravity Ops": 0,
    "Pilot": 0,
    "Torture": 0
}

SECONDARY_KNOWLEDGES = {
    "Area Knowledge": 0,
    "Cultural Savvy": 0,
    "Cybernetics": 0,
    "Demolitions": 0,
    "Herbalism": 0,
    "Hypertech": 0,
    "Media": 0,
    "Paraphysics": 0,
    "Power-Brokering": 0,
    "Vice": 0,
    "Xenobiology": 0
}

SPLAT_SPECIFIC_POWERS = {
    'discipline',      # Vampire, Ghoul
    'combodiscipline', # Vampire
    'thaumaturgy',    # Vampire, Ghoul (sometimes)
    'gift',           # Shifter, Kinfolk, Possessed
    'rite',           # Shifter, Kinfolk
    'art',            # Changeling, Kinain
    'realm',          # Changeling, Kinain
    'sliver',         # inanimae (changeling type)
    'blessing',       # Possessed
    'charm',          # Possessed/Companion
    'sphere',         # Mage
    'special_advantage', # Companion
    'thaum_ritual',   # vampire
    'hedge_ritual',   # sorcerer
    'sorcery',        # sorcerer
    'numina',         # psychic
    'faith'          # faithful
}

POWERS = {
    "Spheres": {
        "Correspondence": 0,
        "Entropy": 0,
        "Forces": 0,
        "Life": 0,
        "Matter": 0,
        "Mind": 0,
        "Prime": 0,
        "Spirit": 0,
        "Time": 0,
        "Dimensional Science": 0,
        "Primal Utility": 0,
        "Data": 0
    },
    "Disciplines": {
        "Celerity": 0,
        "Obfuscate": 0,
        "Quietus": 0,
        "Potence": 0,
        "Presence": 0,
        "Animalism": 0,
        "Protean": 0,
        "Fortitude": 0,
        "Serpentis": 0,
        "Necromancy": 0,
        "Obtenebration": 0,
        "Auspex": 0,
        "Dementation": 0,
        "Chimerstry": 0,
        "Thaumaturgy": 0,
        "Vicissitude": 0
    },
    # Gifts are loaded from JSON files:
    # - diesirae/data/rank1_garou_gifts.json
    # - diesirae/data/rank2_garou_gifts.json
    # - diesirae/data/rank3_garou_gifts.json
    # - diesirae/data/rank4_garou_gifts.json
    # - diesirae/data/rank5_garou_gifts.json
    # - diesirae/data/ajaba_gifts.json
    # - diesirae/data/bastet_gifts.json
    # - diesirae/data/corax_gifts.json
    # - diesirae/data/gurahl_gifts.json
    # - diesirae/data/kitsune_gifts.json
    # - diesirae/data/mokole_gifts.json
    # - diesirae/data/nagah_gifts.json
    # - diesirae/data/nuwisha_gifts.json
    # - diesirae/data/ratkin_gifts.json
    # - diesirae/data/rokea_gifts.json
    "Gifts": {},
    "Realms": {
        "Actor": 0,
        "Fae": 0,
        "Nature": 0,
        "Prop": 0,
        "Scene": 0,
        "Time": 0
    }, 
    "Arts": {
        "Chicanery": 0,
        "Legerdemain": 0,
        "Primal": 0,
        "Pyretics": 0,
        "Soothsay": 0,
        "Sovereign": 0,
        "Spring": 0,
        "Summer": 0,
        "Autumn": 0,
        "Winter": 0,
        "Wayfare": 0,
        "Oneiromancy": 0,
        "Skycraft": 0,
        "Tale Craft": 0,
        "Chronos": 0,
        "Dragon's Ire": 0,
        "Metamorphosis": 0,
        "Contract": 0,
        "Infusion": 0,
        "Kryos": 0,
        "Storm Craft": 0
    },
    "Rites": {},
    "Sorcery": {
        "Alchemy": 0,
        "Conjuration": 0,
        "Chronomancy": 0,
        "Conveyance": 0,
        "Divination": 0,
        "Enchantment": 0,
        "Fascination": 0,
        "Fortune": 0,
        "Gauntlet Manipulation": 0,
        "Healing": 0,
        "Hellfire": 0,
        "Mana Manipulation": 0,
        "Ephemera": 0,
        "Mortal Necromancy": 0,
        "Necronics": 0,
        "Oneiromancy": 0,
        "Saturnal Anima": 0,
        "Saturnal Manes": 0,
        "Scrying": 0,
        "Shadows": 0,
        "Shapeshifting": 0,
        "Spirit Awakening": 0,
        "Spirit Chasing": 0,
        "Starlight": 0,
        "Summoning, Binding, and Warding": 0,
        "Weather Control": 0,
        "Maelstroms": 0
    },
    "Numina": {
        "Animal Psychic": 0,
        "Anti-Psi": 0,
        "Astral Projection": 0,
        "Biocontrol": 0,
        "Channeling": 0,
        "Clairvoyance": 0,
        "Cyberkinesis": 0,
        "Cyberpathy": 0,
        "Ectoplasmic Generation": 0,
        "Empathic Healing": 0,
        "Mind Shields": 0,
        "Precognition": 0,
        "Psychic Healing": 0,
        "Psychic Hypnosis": 0,
        "Psychic Invisibility": 0,
        "Psychic Vampirism": 0,
        "Psychokinesis": 0,
        "Psychometry": 0,
        "Psychoportation": 0,
        "Pyrokinesis": 0,
        "Soul Stealing": 0,
        "Synergy": 0,
        "Telepathy": 0,
    },
    "Faith": {
        "Signs of Faith": 0,
        "Sin-Eating": 0,
        "Faithful Resolve": 0,
        "Words of Faith": 0,
        "Martyrdom": 0,
        "Sanctification": 0,
        "Prophecy": 0,
        "Healing Devotion": 0,
    },
    "Charms": {
        "Airt Sense": 0,
        "Appear": 0,
        "Blast": 0,
        "Blighted Touch": 0,
        "Brand": 0,
        "Break Reality": 0,
        "Calcify": 0,
        "Call for Aid": 0,
        "Cleanse the Blight": 0,
        "Cling Charm": 0,
        "Control Electrical Systems": 0,
        "Corruption": 0,
        "Create Fire Charm": 0,
        "Create Wind Charm": 0,
        "Death Fertility": 0,
        "Digital Disruption": 0,
        "Disable": 0,
        "Disorient": 0,
        "Dream Journey": 0,
        "Ease Pain": 0,
        "Element Sense": 0,
        "Feedback": 0,
        "Flee": 0,
        "Flood": 0,
        "Freeze": 0,
        "Healing Charm": 0,
        "Illuminate": 0,
        "Influence Charm": 0,
        "Inhabit": 0,
        "Insight Charm": 0,
        "Iron Will Charm": 0,
        "Lightning Bolt": 0,
        "Materialize": 0,
        "Meld": 0,
        "Mind Speech Charm": 0,
        "Open Moon Bridge Charm": 0,
        "Peek": 0,
        "Possession Charm": 0,
        "Quake": 0,
        "Re-form": 0,
        "Shapeshift Charm": 0,
        "Short Out": 0,
        "Shatter Glass": 0,
        "Solidify Reality": 0,
        "Spirit Away": 0,
        "Spirit Static": 0,
        "Swift Flight": 0,
        "System Havoc": 0,
        "Terror": 0,
        "Track": 0,
        "Tremor": 0,
        "Umbral Storm": 0,
        "Umbraquake": 0,
        "Updraft": 0,
        "Waves": 0,
    },
    "Special Advantages": {
        "Alacrity": 0,
        "Armor": 0,
        "Aww!": 0,
        "Companion Acute Smell": 0,
        "Bare Necessities": 0,
        "Bioluminescence": 0,
        "Blending": 0,
        "Bond-Sharing": 0,
        "Cause Insanity": 0,
        "Chameleon Coloration": 0,
        "Companion Natural Weaponry": 0,
        "Deadly Demise": 0,
        "Soul-Sense": 0,
        "Dominance": 0,
        "Earthbond": 0,
        "Elemental Touch": 0,
        "Companion Enhancement": 0,
        "Empathic Bond": 0,
        "Extra Heads": 0,
        "Extra Limbs": 0,
        "Feast of Nettles": 0,
        "Ferocity": 0,
        "Ghost Form": 0,
        "Mesmerism": 0,
        "Musical Influence": 0,
        "Musk": 0,
        "Mystic Shield": 0,
        "Needleteeth": 0,
        "Companion Nightsight": 0,
        "Omega Status": 0,
        "Paradox Nullification": 0,
        "Quills": 0,
        "Rapid Healing": 0,
        "Razorskin": 0,
        "Read and Write": 0,
        "Regrowth": 0,
        "Shapechanger": 0,
        "Shared Knowledge": 0,
        "Spirit Travel": 0,
        "Spirit Vision": 0,
        "Soak Lethal Damage": 0,
        "Soak Aggravated Damage": 0,
        "Tunneling": 0,
        "Unaging": 0,
        "Universal Translator": 0,
        "Venom": 0,
        "Wall-Crawling": 0,
        "Water Breathing": 0,
        "Webbing": 0,
        "Companion Wings": 0,
        "Hibernation": 0,
        "Immunity": 0,
        "Information Fount": 0,
        "Intangibility": 0,
        "Healing Lick": 0,
        "Human Speech": 0,
        "Human Guise": 0,
        "Flexible": 0,
        "Telepathy": 0,
        "Telekinesis": 0,
        "Tides of Fortune": 0,
        "Speed": 0        
    },
    "Blessings": {
        "Animal Control": 0,
        "Armored Hide": 0,
        "Armored Skin": 0,
        "Aura of Tranquility": 0,
        "Addictive Personality": 0,
        "Reassuring Presence": 0,
        "Bestial Mutation": 0,
        "Berserker": 0,
        "Darksight": 0,
        "Extra Speed": 0,
        "Footpads": 0,
        "Homogeneity": 0,
        "Immunity to the Delirium": 0,
        "Mega-Attribute": 0,
        "Nimbleness": 0,
        "Sense the Unnatural": 0,
        "Size": 0,
        "Size Shift": 0,
        "Shapeshifter Kin": 0,
        "Spirit Charm": 0,
        "Spirit Ties": 0,
        "Umbral Passage": 0,
        "Wall Walking": 0,
        "Water Breathing": 0,
        "Webbing": 0,
        "Beast of Burden": 0,
        "Curse of Gaia": 0,
        "Possessed Wings": 0,
        "Elemental Resistance": 0,
        "Heart Sense": 0,
        "Longevity": 0,
        "Mercy": 0,
        "Piercing Gaze": 0,
        "Plant Animation": 0,
        "Plant Kinship": 0,
        "Ritekeeper": 0,
        "Season's Blessing": 0,
        "Spirit Awakening": 0,
        "Spirit Kinship": 0,
        "Spirit Sense": 0,
        "Transformation": 0,
        "Triatic Sense": 0,
        "Universal Tongue": 0,
        "Body-Barbs": 0,
        "Body Expansion": 0,
        "Brain Eating": 0,
        "Cancerous Carapace": 0,
        "Cause Insanity": 0,
        "Chameleon Coloration": 0,
        "Claws and Fangs": 0,
        "Deception": 0,
        "Dentata Orifice": 0,
        "Echoes of Wrath": 0,
        "Ectoplasmic Extrusion": 0,
        "Exoskeleton": 0,
        "Possessed Extra Limbs": 0,
        "Eyes of the Wyrm": 0,
        "Fiery Discharge": 0,
        "Fungal Touch": 0,
        "Fungal Udder": 0,
        "Hazardous Breath": 0,
        "Hell's Hide": 0,
        "Infectious Touch": 0,
        "Invisibility": 0,
        "Lashing Tail": 0,
        "Malleate": 0,
        "Maw of the Wyrm": 0,
        "Mind Blast": 0,
        "Molecular Weakening": 0,
        "Noxious Breath": 0,
        "Noxious Miasma": 0,
        "Numbing": 0,
        "Phoenix Form": 0,
        "Poison Tumors": 0,
        "Rat Head": 0,
        "Regeneration": 0,
        "Roar of the Wyrm": 0,
        "Sense Gaia": 0,
        "Shadowplay": 0,
        "Skittersight": 0,
        "Slither Skin": 0,
        "Slobbersnot": 0,
        "Stomach Pumper": 0,
        "Tar Skin": 0,
        "Toxic Secretions": 0,
        "Triatic Mask": 0,
        "Twisted Senses": 0,
        "Unnatural Strength": 0,
        "Venomous Bite": 0,
        "Viscous Form": 0,
        "Voice of the Wyrm": 0,
        "Wrathful Invective": 0
    }
}

BACKGROUNDS = {
    "Allies": 0,
    "Contacts": 0,
    "Fame": 0,
    "Influence": 0,
    "Resources": 0,
    "Fate": 0,
    "Artifact": 0,
    "Mob": 0,
    "Base of Operations": 0,
    "Guide": 0,
    "Spirit Ridden": 0,
    "Cult": 0,
    "Armory": 0,
    "Equipment": 0,
    "Servants": 0,
    "Organizational Rank": 0,
    "Spies": 0,
    "Totem": 0,
    "Reliquary": 0,
    "Backup": 0,
    "Certification": 0,
    "Library": 0,
    "Secrets": 0,
    
#Vampire Backgrounds
    "Anarch Information Exchange": 0,
    "Black Hand Membership": 0,
    "Communal Haven": 0,
    "Ritae": 0,
    "Blasphemous Shrine": 0,
    "Memento de Morte": 0,
    "Spirit Slaves": 0,
    "Oubliette": 0,
    "Herd": 0,
    "Generation": 0,

#Changeling Backgrounds
    "Chimerical Companion": 0,
    "Dreamers": 0,
    "Title": 0,
    "Digital Dreamers": 0,
    "Holdings": 0,
    "Remembrance": 0,
    "Retinue": 0,
    "Treasure": 0,
    "Chimerical Item": 0,
    "Vision": 0,
    "Spirit Companion": 0,
    "Circle": 0,
    "Husk": 0,
    "Changeling Companion": 0,

#Mage/Companion Backgrounds
    "Familiar": 0,
    "Blessing": 0,
    "Companion": 0,
    "Legend": 0,
    "Avatar": 0,
    "Genius": 0,
    "Node": 0,
    "Past Lives": 0,
    "Chantry": 0,
    "Labyrinth": 0,
    "Construct": 0,
    "Enhancement": 0,
    "Patron": 0,
    "Secret Weapons": 0,
    "Alternate Identity": 0,
    "Arcane": 0,
    "Cloaking": 0,
    "Demesne": 0,
    "Destiny": 0,
    "Dream": 0,
    "Hypercram": 0,
    "Laboratory": 0,
    "Requisitions": 0,
    "Sanctum": 0,
    "Wonder": 0,
    "Years": 0,

#Shifter Backgrounds
    "Ancestors": 0,
    "Fetish": 0,
    "Kinfolk": 0,
    "Pure Breed": 0,
    "Jamak": 0,
    "Rites": 0,
    "Spirit Heritage": 0,
    "Umbral Glade": 0,
    "Mnesis": 0,
    "Wallow": 0,
    "Den-Realm": 0,
    "Umbral Maps": 0,
    "Kitsune Clan": 0,
    "Go-En": 0,
    "Sempai": 0,

#Mortalplus Backgrounds
    "Techne": 0,
    "Antecessor": 0,
    "Paranormal Tools": 0,
    "Caretaker": 0
}
# Merits are loaded from JSON files:
# - diesirae/data/changeling_merits.json
# - diesirae/data/fera_merits.json
# - diesirae/data/garou_merits.json
# - diesirae/data/mage_merits.json
# - diesirae/data/mortalplus_merits.json
# - diesirae/data/vampire_merits.json
MERITS = {}

# Flaws are loaded from JSON files:
# - diesirae/data/changeling_flaws.json
# - diesirae/data/fera_flaws.json
# - diesirae/data/garou_flaws.json
# - diesirae/data/mage_flaws.json
# - diesirae/data/mortalplus_flaws.json
# - diesirae/data/vampire_flaws.json
FLAWS = {}

HEALTH = {
    "Bruised": False,
    "Hurt": False,
    "Injured": False,
    "Wounded": False,
    "Mauled": False,
    "Crippled": False,
    "Incapacitated": False
}

RENOWN = {
    "Glory": 0,
    "Honor": 0,
    "Wisdom": 0,
    "Cunning": 0,
    "Ferocity": 0,
    "Obligation": 0, 
    "Obedience": 0, 
    "Humor": 0, 
    "Infamy": 0, 
    "Valor": 0, 
    "Harmony": 0, 
    "Innovation": 0
}

SHIFTER_TYPE = {
    'Garou', 'Ajaba', 'Bastet', 'Rokea', 'Ananasi', 'Corax', 'Gurahl',
    'Kitsune', 'Mokole', 'Camazotz', 'Nuwisha', 'Ratkin', 'Nagah'
}

KITH = {
    'Boggan', 'Clurichaun', 'Eshu', 'Nocker', 'Piskie', 'Pooka', 'Redcap', 'Satyr', 
    'Selkie', 'Arcadian Sidhe', 'Autumn Sidhe', 'Sluagh', 'Troll', 'Nunnehi', 'Inanimae'
}

CLAN = {
    'Brujah', 'Gangrel', 'Malkavian', 'Nosferatu', 'Toreador', 'Tremere', 'Ventrue', 'Lasombra', 
    'Tzimisce', 'Assamite', 'Followers of Set', 'Hecata', 'Ravnos', 'Baali', 'Blood Brothers', 
    'Daughters of Cacophony', 'Gargoyles', 'Kiasyd', 'Nagaraja', 'Salubri', 'Samedi', 'True Brujah'
}

BREED = {
    'Homid', 'Metis', 'Animal-Born'
}

GAROU_TRIBE = {
    'Shadow Lord', 'Glass Walker', 'Uktena', 'Bone Gnawer', 'Children of Gaia',
    'Black Fury', 'Silver Fang', 'Get of Fenris', 'Silent Strider',
    'Fianna', 'Wendigo', 'Stargazer', 'Hakken'
}

ROKEA_AUSPICE = {
    'Brightwater', 'Dimwater', 'Darkwater'
}

ROKEA_TRIBE = {
    'Traditionalist', 'Betweener', 'Same-Bito'
}

AJABA_ASPECTS = {
    'Dawn', 'Midnight', 'Dusk'
}
AJABA_FACTION = {
    'Ozuzo', 'Gaian'
}

ANANASI_ASPECT = {
    'Tenere', 'Hatar', 'Kumoti'
}

ANANASI_FACTION = {
    'Myrmidon', 'Viskr', 'Wyrsta'
}

ANANASI_CABAL = {
    'Secean', 'Plicare', 'Gaderin', 'Agrere', 'Anomia', 'Malum', 'Kar', 'Amari Aliquid', 
    'Chymos', 'Kumo', 'Antara', 'Kumatai', 'Padrone'
}

GURAHL_AUSPICE = {
    'Arcas', 'Uzmati', 'Kojubat', 'Kieh', 'Rishi'
}

GURAHL_TRIBE = {
    'Forest Walkers', 'Ice Stalkers', 'Mountain Guardians', 'River Keepers', 'Okuma'
}

KITSUNE_PATHS = {
    'Eji', 'Doshi', 'Gukutsushi', 'Kataribe'
}

KITSUNE_FACTIONS = {
    'Emerald Courts', 'Western Courts'
}

VARNA = {
    'Champsa', 'Halpatee', 'Piasa', 'Syrta', 'Unktehi', 'Karna', 'Ora', 'Gharial', 'Karna',
    'Makara', 'Lung'
}

MOKOLE_AUSPICE = {
    'Rising Sun', 'Noonday Sun', 'Shrouded Sun', 'Midnight Sun', 'Decorated Sun', 'Solar Eclipse'
}

MOKOLE_STREAMS = {
    'Gumagan', 'Mokole-mbembe', 'Zhong Lung', 'Makara'
}

RATKIN_ASPECTS = {
    'Knife Skulkers', 'Shadow Seers', 'Tunnel Runners', 'Warriors'
}

RATKIN_PLAGUES = {
    'Borrachon Wererats', "De La Poer's Disciples", 'Gamine', 
    'Horde', 'Nezumi', 'Ratkin Ronin', 'Rat Race', 'Rattus Typhus', 'Thuggees'
}

NAGAH_AUSPICE = {
    'Kamakshi', 'Kartikeya', 'Kamsa', 'Kali'
}

NAGAH_CROWNS = {
    'Nemontana', 'Zuzeka', 'Jurlungur', 'Vritra', 'Yamilka', 'Sayidi'
}

GAROU_TRIBE = {
    'Shadow Lord', 'Glass Walker', 'Uktena', 'Bone Gnawer', 'Children of Gaia',
    'Black Fury', 'Silver Fang', 'Get of Fenris', 'Silent Strider',
    'Fianna', 'Wendigo', 'Stargazer', 'Hakken'
}

GAROU_AUSPICE = {
    'Ragabash', 'Galliard', 'Theurge', 'Ahroun', 'Philodox'
}

AFFILIATION = {
    'Traditions', 'Technocracy', 'Nephandi'
}

TRADITION = {
    'Cultists of Ecstasy', 'Euthanatos', 'Celestial Chorus', 'Akashic Brotherhood',
    'Dreamspeakers', 'Virtual Adepts', 'Order of Hermes', 'Verbena',
    'Sons of Ether'
}

TRADITION_SUBFACTION = {
    'Akashic_Brotherhood': [
    'Chabnagpa', 'Lin Shen', 'Wu Shan', 'Yamabushi', 'Jina', 'Karmachakra', 'Shaolin', 'Blue Skins',
    'Mo-Tzu Fa', "Roda d'Oro", 'Gam Lung', 'Han Fei Tzu Academy', 'Kaizankai', 'Banner of the Ebon Dragon', 
    'Sulsa', 'Tenshi Arashi Ryu', 'Wu Lung'
    ],
    'Celestial Chorus': [
    'Brothers of St. Christopher', 'Chevra Kedisha', 'Knights of St. George', 'Order of St. Michael', 
    'Poor Knights of the Temple of Solomon', 'Sisters of Gabrielle', 'Alexandrian Society', 'Anchorite',
    'Children of Albi', 'Latitudinarian', 'Monist', 'Nashimite', 'Septarian', 'Hare Krishna', 'Hindu',
    'Jain', 'Son of Mithras', 'Rastafarian', 'Sikh', 'Sufi', 'Bat Binah', 'Song of the Ancients'
    ],
    'Cultists of Ecstasy': [
    'Erzuli Jingo', 'Kiss of Astarte', 'Maenad', "K'an Lu", 'Vratyas', 'Aghoris', 'Acharne', 'Freyji',
    'Sons of Wotan', 'Sutr', 'Joybringers', 'Dissonance Society', 'Klubwerks', "Children's Crusade",
    'Cult of Acceptance', 'Silver Bridges', 'Los Sabios Locos', "Ka'a", 'Khlysty Flagellants', 
    "Bongo's Rangers", 'Dervish', 'Confrerie Chango', 'Roda do Jogo', 'Los Sangradores', 'Studiosi',
    'Umilyenye'
    ],
    'Euthanatos': [
    'Aided', 'Devasu', 'Lhakmist', 'Natatapa', 'Knight of Radamanthys', 'Pomegranate Deme', "N'anga",
    'Ta Kiti', 'Albireo', 'Chakramuni', 'Golden Chalice', 'Pallottino', 'Scholars of the Wheel', "Yggdrasil's Keepers",
    'Yum Cimil'
    ],
    'Dreamspeakers': [
    'Balomb', 'Baruti', 'Contrary', 'Four Winds', 'Ghost Wheel Society', 'Keeper of the Sacred Fire', 
    'Kopa Loei', 'Red Spear Society', 'Sheikha', 'Solitaries', 'Spirit Smith', 'Uzoma'
    ],
    'Order of Hermes': [
    'House Bonisagus', 'House Flambeau', 'House Fortunae', 'House Quaesitori', 'House Shaea', 'House Tytalus',
    'House Verditius', 'House Criamon', 'House Jerbiton', 'House Merinita', 'House Skopos', 'House Xaos'
    ],
    'Verbena': [
    'Gardeners of the Tree', 'Lifeweavers', 'Moon-Seekers', 'Twisters of Fate', 'Techno-Pagans', 'Fairy Folk', 'New Age'
    ],
    'Sons of Ether': [
    'Ethernauts', 'Cybernauts', 'Utopians', 'Adventurers', 'Mad Scientists', 'Progressivists', 'Aquanauts'
    ],
    'Virtual Adepts': [
    'Chaoticians', 'Cyberpunk', 'Cypherpunks', 'Nexplorers', 'Reality Coders'
    ]
}

CONVENTION = {
    'Iteration X', 'New World Order', 'Progenitor', 'Syndicate', 'Void Engineer'
}

METHODOLOGIES = {
    'Iteration X': [
    'BioMechanics', 'Macrotechnicians', 'Statisticians', 'Time-Motion Managers'
    ],
    'New World Order': [
    'Ivory Tower', 'Operatives', 'Watchers', 'The Feed', 'Q Division', 'Agronomists'
    ],
    'Progenitors': [
    'Applied Sciences', 'Deviancy Scene investigators', 'Médecins Sans Superstition',
    'Biosphere Explorers', 'Damage Control', 'Ethical Compliance', 'FACADE Engineers',
    'Genegineers', 'Pharmacopoeists', 'Preservationists', 'Psychopharmacopoeists', 
    'Shalihotran Society'
    ],
    'Syndicate': [
    'Disbursements', 'Assessment Division', 'Reorganization Division', 'Procurements Division',
    'Extraction Division', 'Enforcers (Hollow Men)', 'Legal Division', 'Extralegal Division',
    'Extranational Division', 'Information Specialists', 'Special Information Security Division',
    'Financiers', 'Acquisitions Division', 'Entrepreneurship Division', 'Liquidation Division',
    'Media Control', 'Effects Division', 'Spin Division', 'Marketing Division', 'Special Projects Division'
    ],
    'Void Engineer': [
    'Border Corps Division', 'Earth Frontier Division', 'Aquatic Exploration Teams',
    'Cryoregional Specialists', 'Hydrothermal Botanical Mosaic Analysts', 'Inaccessible High Elevation Exploration Teams',
    'Subterranean Exploration Corps', 'Neutralization Specialist Corps', 'Neutralization Specialists', 
    'Enforcement Training and Conditioning Agency', 'Department of Psychological Evaluation and Maintenance', 'Pan-Dimensional Corps', 
    'Deep Exploration Teams', 'Solar Exploration Teams', 'Cybernauts', 'Chrononauts', 'Research & Execution'
    ]
}

NEPHANDI_FACTION = {
    'Herald of the Basilisk', 'Obliviate', 'Malfean', 'Baphie', 'Infernalist', 'Ironhand', 'Mammonite', "K'llashaa"
}

SECT = {
    'Sabbat', 'Camarilla', 'Anarch', 'Independent'
}

SEEMING = {
    'Childling', 'Wilder', 'Grump'
}

PATHS_OF_ENLIGHTENMENT = {
    "humanity": "Humanity",
    "path_of_blood": "Path of Blood",
    "path_of_bones": "Path of Bones",
    "path_of_the_beast": "Path of the Beast",
    "path_of_harmony": "Path of Harmony",
    "path_of_evil_revelations": "Path of Evil Revelations",
    "path_of_self_focus": "Path of Self-Focus",
    "path_of_the_scorched_heart": "Path of the Scorched Heart",
    "path_of_entelechy": "Path of Entelechy",
    "sharia_el_sama": "Sharia El-Sama",
    "hierarchy_of_wyrm_taint": "Hierarchy of Wyrm Taint",
    "path_of_asakku": "Path of Asakku",
    "path_of_death_and_the_soul": "Path of Death and the Soul",
    "path_of_honorable_accord": "Path of Honorable Accord",
    "path_of_the_feral_heart": "Path of the Feral Heart",
    "path_of_orion": "Path of Orion",
    "path_of_power_and_the_inner_voice": "Path of Power and the Inner Voice",
    "path_of_lilith": "Path of Lilith",
    "path_of_caine": "Path of Caine",
    "path_of_cathari": "Path of Cathari",
    "path_of_redemption": "Path of Redemption",
    "path_of_nocturnal_redemption": "Path of Nocturnal Redemption",
    "path_of_the_sun": "Path of the Sun",
    "path_of_night": "Path of Night",
    "path_of_metamorphosis": "Path of Metamorphosis",
    "path_of_typhon": "Path of Typhon",
    "path_of_paradox": "Path of Paradox",
    "path_of_the_hive": "Path of the Hive"
}

ATTRIBUTES = {
    "Strength": 1,
    "Dexterity": 1,
    "Stamina": 1,
    "Charisma": 1,
    "Manipulation": 1,
    "Appearance": 1,
    "Perception": 1,
    "Intelligence": 1,
    "Wits": 1
}

ABILITIES = {
    "Talents": TALENTS,
    "Skills": SKILLS,
    "Knowledges": KNOWLEDGES
}

SECONDARY_ABILITIES = {
    "Secondary Talents": SECONDARY_TALENTS,
    "Secondary Skills": SECONDARY_SKILLS,
    "Secondary Knowledges": SECONDARY_KNOWLEDGES
}

ADVANTAGES = {
    "Backgrounds": BACKGROUNDS,
    "Virtues": {
        "Conscience": 1,
        "Self-Control": 1,
        "Courage": 1,
        "Conviction": 0,
        "Instict": 0
    },
    "Willpower": 1
}

POOLS = {
    
}