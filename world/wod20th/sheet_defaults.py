# world/characters/sheet_defaults.py
from  utils.sheet_constants import BACKGROUNDS, MERITS, FLAWS
TALENTS = {
    "Alertness": 0,
    "Athletics": 0,
    "Awareness": 0,
    "Brawl": 0,
    "Empathy": 0,
    "Expression": 0,
    "Intimidation": 0,
    "Leadership": 0,
    "Stealth": 0,
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
    "Survival": 0,
    "Technology": 0
}

KNOWLEDGES = {
    "Academics": 0,
    "Bureaucracy": 0,
    "Computer": 0,
    "Enigmas": 0,
    "Finance": 0,
    "Investigation": 0,
    "Law": 0,
    "Medicine": 0,
    "Occult": 0,
    "Politics": 0,
    "Science": 0
}

SECONDARY_TALENTS = {
    "Carousing": 0,
    "Diplomacy": 0,
    "Intrigue": 0,
    "Mimicry": 0,
    "Scrounging": 0,
    "Seduction": 0,
    "Style": 0
}

SECONDARY_SKILLS = {
    "Archery": 0,
    "Fortune-Telling": 0,
    "Fencing": 0,
    "Gambling": 0,
    "Jury-Rigging": 0,
    "Pilot": 0,
    "Torture": 0
}

SECONDARY_KNOWLEDGES = {
    "Area Knowledge": 0,
    "Cultural Savvy": 0,
    "Demolitions": 0,
    "Herbalism": 0,
    "Media": 0,
    "Power-Brokering": 0,
    "Vice": 0
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
        "Time": 0
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
        "Vicissitude": 0,
        "Abombwe": 0,
        "Bardo": 0,
        "Daimonion": 0,
        "Deimos": 0,
        "Kai": 0,
        "Kineticism": 0,
        "Maleficia": 0,
        "Melpominee": 0,
        "Mytherceria": 0,
        "Nihilistics": 0,
        "Obeah": 0,
        "Rift": 0,
        "Sanguinus": 0,
        "Spiritus": 0,
        "Striga": 0,
        "Temporis": 0,
        "Thanatosis": 0,
        "Valeren": 0,
        "Visceratika": 0
    },
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
        "Naming": 0,
        "Oneiromancy": 0,
        "Skycraft": 0,
        "Tale Craft": 0,
        "Chronos": 0,
        "Dragon's Ire": 0,
        "Metamorphosis": 0,
        "Contract": 0
    }
}

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
    'Selkie', 'Arcadian Sidhe', 'Autumn Sidhe', 'Sluagh', 'Troll', 'Inanimae', 'Hsien', 'Nunnehi',
    'Korred', 'River Hag', 'Swan Maiden', 'Encanto', 'Sachamama', 'Morganed', 'Alicanto', 'Boraro', 
    'Llorona', 'Merfolk', 'Wichtel', 'Wolpertinger'
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

VARNAS = {
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
    'Iteration_X': [
    'BioMechanics', 'Macrotechnicians', 'Statisticians', 'Time-Motion Managers'
    ],
    'NEW_WORLD_ORDER': [
    'Ivory Tower', 'Operatives', 'Watchers', 'The Feed', 'Q Division', 'Agronomists'
    ],
    'PROGENITORS': [
    'Applied Sciences', 'Deviancy Scene investigators', 'Médecins Sans Superstition',
    'Biosphere Explorers', 'Damage Control', 'Ethical Compliance', 'FACADE Engineers',
    'Genegineers', 'Pharmacopoeists', 'Preservationists', 'Psychopharmacopoeists', 
    'Shalihotran Society'
    ],
    'SYNDICATE': [
    'Disbursements', 'Assessment Division', 'Reorganization Division', 'Procurements Division',
    'Extraction Division', 'Enforcers (Hollow Men)', 'Legal Division', 'Extralegal Division',
    'Extranational Division', 'Information Specialists', 'Special Information Security Division',
    'Financiers', 'Acquisitions Division', 'Entrepreneurship Division', 'Liquidation Division',
    'Media Control', 'Effects Division', 'Spin Division', 'Marketing Division', 'Special Projects Division'
    ],
    'VOID_ENGINEER': [
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
    'Childling', 'Wilder', 'Grump', 'Youngling', 'Brave', 'Elder'
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

ADVANTAGES = {
    "Backgrounds": BACKGROUNDS,
    "Virtues": {
        "Conscience": 1,
        "Self-Control": 1,
        "Courage": 1
    },
    "Willpower": 1
}