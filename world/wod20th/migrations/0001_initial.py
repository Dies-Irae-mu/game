# Generated by Django 4.2.13 on 2025-01-13 01:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("objects", "0014_defaultobject_crisis_defaultcharacter_defaultexit_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ActionTemplate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField()),
                ("downtime_cost", models.IntegerField(default=0)),
                ("requires_target", models.BooleanField(default=False)),
                ("category", models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Asset",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                (
                    "asset_type",
                    models.CharField(
                        choices=[
                            ("retainer", "Retainer"),
                            ("haven", "Haven"),
                            ("territory", "Territory"),
                            ("contact", "Contact"),
                        ],
                        max_length=50,
                    ),
                ),
                ("description", models.TextField(blank=True, null=True)),
                ("value", models.IntegerField(default=0)),
                ("owner_id", models.IntegerField()),
                ("status", models.CharField(default="Active", max_length=50)),
                ("traits", models.JSONField(blank=True, default=dict, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Stat",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(default="")),
                ("game_line", models.CharField(max_length=100)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("attributes", "Attributes"),
                            ("abilities", "Abilities"),
                            ("secondary_abilities", "Secondary Abilities"),
                            ("advantages", "Advantages"),
                            ("backgrounds", "Backgrounds"),
                            ("powers", "Powers"),
                            ("merits", "Merits"),
                            ("flaws", "Flaws"),
                            ("traits", "Traits"),
                            ("identity", "Identity"),
                            ("archetype", "Archetype"),
                            ("virtues", "Virtues"),
                            ("legacy", "Legacy"),
                            ("pools", "Pools"),
                            ("other", "Other"),
                        ],
                        max_length=100,
                    ),
                ),
                (
                    "stat_type",
                    models.CharField(
                        choices=[
                            ("attribute", "Attribute"),
                            ("ability", "Ability"),
                            ("secondary_ability", "Secondary Ability"),
                            ("advantage", "Advantage"),
                            ("background", "Background"),
                            ("lineage", "Lineage"),
                            ("discipline", "Discipline"),
                            ("combodiscipline", "Combo Discipline"),
                            ("gift", "Gift"),
                            ("rite", "Rite"),
                            ("sphere", "Sphere"),
                            ("rote", "Rote"),
                            ("art", "Art"),
                            ("splat", "Splat"),
                            ("edge", "Edge"),
                            ("discipline", "Discipline"),
                            ("realm", "Realm"),
                            ("sphere", "Sphere"),
                            ("art", "Art"),
                            ("path", "Path"),
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
                            ("paradox", "Paradox"),
                            ("kith", "Kith"),
                            ("seeming", "Seeming"),
                            ("house", "House"),
                            ("seelie-legacy", "Seelie Legacy"),
                            ("unseelie-legacy", "Unseelie Legacy"),
                        ],
                        max_length=100,
                    ),
                ),
                ("values", models.JSONField(blank=True, default=list, null=True)),
                (
                    "lock_string",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "splat",
                    models.CharField(
                        blank=True, default=None, max_length=100, null=True
                    ),
                ),
                ("hidden", models.BooleanField(default=False)),
                ("locked", models.BooleanField(default=False)),
                ("instanced", models.BooleanField(default=False, null=True)),
                (
                    "default",
                    models.CharField(
                        blank=True, default=None, max_length=100, null=True
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ShapeshifterForm",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                ("shifter_type", models.CharField(max_length=50)),
                ("description", models.TextField()),
                ("stat_modifiers", models.JSONField(default=dict)),
                ("rage_cost", models.IntegerField(default=0)),
                ("difficulty", models.IntegerField(default=6)),
                (
                    "lock_string",
                    models.CharField(
                        default="examine:all();control:perm(Admin)", max_length=255
                    ),
                ),
            ],
            options={
                "unique_together": {("name", "shifter_type")},
            },
        ),
        migrations.CreateModel(
            name="CharacterSheet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "account",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="character_sheet",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "character",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="character_sheet",
                        to="objects.objectdb",
                    ),
                ),
                (
                    "db_object",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="db_character_sheet",
                        to="objects.objectdb",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Action",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("character_id", models.IntegerField()),
                ("downtime_spent", models.IntegerField(default=0)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=10,
                    ),
                ),
                ("result", models.TextField(blank=True, null=True)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "target_asset",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="targeted_by_actions",
                        to="wod20th.asset",
                    ),
                ),
                (
                    "template",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="wod20th.actiontemplate",
                    ),
                ),
            ],
        ),
    ]
