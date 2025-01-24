# Generated by Django 4.2.16 on 2025-01-22 17:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wod20th", "0010_characterimage"),
    ]

    operations = [
        migrations.AlterField(
            model_name="stat",
            name="stat_type",
            field=models.CharField(
                choices=[
                    ("attribute", "Attribute"),
                    ("ability", "Ability"),
                    ("secondary_ability", "Secondary Ability"),
                    ("advantage", "Advantage"),
                    ("background", "Background"),
                    ("lineage", "Lineage"),
                    ("discipline", "Discipline"),
                    ("combodiscipline", "Combo Discipline"),
                    ("thaumaturgy", "Thaumaturgy"),
                    ("gift", "Gift"),
                    ("rite", "Rite"),
                    ("sphere", "Sphere"),
                    ("rote", "Rote"),
                    ("art", "Art"),
                    ("splat", "Splat"),
                    ("edge", "Edge"),
                    ("bygone_power", "Bygone Power"),
                    ("discipline", "Discipline"),
                    ("realm", "Realm"),
                    ("sphere", "Sphere"),
                    ("art", "Art"),
                    ("path", "Path"),
                    ("sorcery", "Sorcery"),
                    ("faith", "Faith"),
                    ("numina", "Numina"),
                    ("enlightenment", "Enlightenment"),
                    ("power", "Power"),
                    ("other", "Other"),
                    ("virtue", "Virtue"),
                    ("vice", "Vice"),
                    ("merit", "Merit"),
                    ("flaw", "Flaw"),
                    ("trait", "Trait"),
                    ("skill", "Skill"),
                    ("knowledge", "Knowledge"),
                    ("talent", "Talent"),
                    ("secondary_knowledge", "Secondary Knowledge"),
                    ("secondary_talent", "Secondary Talent"),
                    ("secondary_skill", "Secondary Skill"),
                    ("specialty", "Specialty"),
                    ("other", "Other"),
                    ("physical", "Physical"),
                    ("social", "Social"),
                    ("mental", "Mental"),
                    ("personal", "Personal"),
                    ("supernatural", "Supernatural"),
                    ("moral", "Moral"),
                    ("temporary", "Temporary"),
                    ("dual", "Dual"),
                    ("renown", "Renown"),
                    ("arete", "Arete"),
                    ("banality", "Banality"),
                    ("glamour", "Glamour"),
                    ("essence", "Essence"),
                    ("quintessence", "Quintessence"),
                    ("blood", "Blood"),
                    ("rage", "Rage"),
                    ("gnosis", "Gnosis"),
                    ("willpower", "Willpower"),
                    ("resonance", "Resonance"),
                    ("synergy", "Synergy"),
                    ("paradox", "Paradox"),
                    ("kith", "Kith"),
                    ("seeming", "Seeming"),
                    ("house", "House"),
                    ("seelie-legacy", "Seelie Legacy"),
                    ("unseelie-legacy", "Unseelie Legacy"),
                    ("court", "Court"),
                    ("mortalplus_type", "Mortal+ Type"),
                    ("varna", "Varna"),
                ],
                max_length=100,
            ),
        ),
    ]
