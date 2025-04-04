# Generated by Django 4.2.16 on 2025-03-31 17:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("equipment", "0005_landcraft_requires_skill"),
    ]

    operations = [
        migrations.CreateModel(
            name="ThrownWeaponDetails",
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
                ("damage", models.CharField(max_length=100)),
                ("damage_type", models.CharField(max_length=100)),
                ("range", models.CharField(max_length=100)),
                ("difficulty", models.PositiveIntegerField()),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="thrown_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="TechnocraticDeviceDetails",
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
                ("power_source", models.CharField(max_length=100)),
                ("power_level", models.PositiveIntegerField()),
                ("maintenance_required", models.BooleanField(default=True)),
                ("maintenance_interval", models.CharField(max_length=100)),
                ("special_features", models.TextField(blank=True)),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="technocratic_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="SurvivalGearDetails",
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
                ("durability", models.PositiveIntegerField()),
                ("weather_resistance", models.CharField(max_length=100)),
                ("special_features", models.TextField(blank=True)),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="survival_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="SupernaturalItemDetails",
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
                ("power_level", models.PositiveIntegerField()),
                ("activation_requirements", models.TextField()),
                ("duration", models.CharField(max_length=100)),
                ("special_effects", models.TextField()),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="supernatural_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="SpyingDeviceDetails",
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
                ("function", models.CharField(max_length=100)),
                ("battery_life", models.CharField(max_length=100)),
                ("range", models.CharField(max_length=100)),
                ("stealth_rating", models.PositiveIntegerField()),
                ("special_features", models.TextField(blank=True)),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="spying_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="SpecialAmmunitionDetails",
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
                ("damage", models.CharField(max_length=100)),
                ("effects", models.TextField()),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="special_ammo_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="SeacraftDetails",
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
                ("speed", models.CharField(max_length=100)),
                ("range", models.CharField(max_length=100)),
                ("capacity", models.PositiveIntegerField()),
                ("special_features", models.TextField(blank=True)),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="seacraft_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="RangedWeaponDetails",
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
                ("damage", models.CharField(max_length=100)),
                ("damage_type", models.CharField(max_length=100)),
                ("range", models.CharField(max_length=100)),
                ("rate", models.CharField(max_length=100)),
                ("clip", models.PositiveIntegerField()),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ranged_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="MeleeWeaponDetails",
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
                ("damage", models.CharField(max_length=100)),
                ("damage_type", models.CharField(max_length=100)),
                ("difficulty", models.PositiveIntegerField()),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="melee_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="MartialArtsWeaponDetails",
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
                ("damage", models.CharField(max_length=100)),
                ("damage_type", models.CharField(max_length=100)),
                ("difficulty", models.PositiveIntegerField()),
                ("style_requirements", models.TextField(blank=True)),
                ("special_techniques", models.TextField(blank=True)),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="martial_arts_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="LandcraftDetails",
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
                ("safe_speed", models.CharField(blank=True, max_length=100)),
                ("max_speed", models.CharField(blank=True, max_length=100)),
                ("maneuver", models.PositiveIntegerField(blank=True, null=True)),
                ("crew", models.CharField(blank=True, max_length=100)),
                ("durability", models.PositiveIntegerField(blank=True, null=True)),
                ("structure", models.PositiveIntegerField(blank=True, null=True)),
                ("weapons", models.CharField(blank=True, max_length=100)),
                ("requires_skill", models.CharField(default="Drive", max_length=100)),
                (
                    "vehicle_type",
                    models.CharField(
                        choices=[
                            ("truck", "Truck"),
                            ("car", "Car"),
                            ("suv", "SUV"),
                            ("bus", "Bus"),
                            ("tank", "Tank"),
                            ("other", "Other"),
                        ],
                        max_length=50,
                    ),
                ),
                ("mass_damage", models.CharField(blank=True, max_length=100)),
                ("passenger_protection", models.CharField(blank=True, max_length=100)),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="landcraft_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="JetpackDetails",
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
                ("safe_speed", models.PositiveIntegerField()),
                ("max_speed", models.PositiveIntegerField()),
                ("maneuver", models.PositiveIntegerField()),
                ("durability", models.PositiveIntegerField()),
                ("structure", models.PositiveIntegerField()),
                ("requires_skill", models.CharField(default="Jetpack", max_length=100)),
                ("is_technomagickal", models.BooleanField(default=True)),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="jetpack_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ImprovisedWeaponDetails",
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
                ("damage", models.CharField(max_length=100)),
                ("damage_type", models.CharField(max_length=100)),
                ("difficulty", models.PositiveIntegerField()),
                ("break_chance", models.PositiveIntegerField(default=50)),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="improvised_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ExplosiveDetails",
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
                ("blast_area", models.CharField(max_length=100)),
                ("blast_power", models.CharField(max_length=100)),
                ("burn", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True)),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="explosive_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ElectronicDeviceDetails",
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
                ("power_source", models.CharField(max_length=100)),
                ("battery_life", models.CharField(max_length=100)),
                ("special_features", models.TextField(blank=True)),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="electronic_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CycleDetails",
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
                ("safe_speed", models.CharField(blank=True, max_length=100)),
                ("max_speed", models.CharField(blank=True, max_length=100)),
                ("maneuver", models.PositiveIntegerField(blank=True, null=True)),
                ("crew", models.CharField(blank=True, max_length=100)),
                ("durability", models.PositiveIntegerField(blank=True, null=True)),
                ("structure", models.PositiveIntegerField(blank=True, null=True)),
                ("weapons", models.CharField(blank=True, max_length=100)),
                ("requires_skill", models.CharField(default="Drive", max_length=100)),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cycle_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CommunicationsDeviceDetails",
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
                ("range", models.CharField(max_length=100)),
                ("encryption_level", models.PositiveIntegerField()),
                ("battery_life", models.CharField(max_length=100)),
                ("special_features", models.TextField(blank=True)),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="communications_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ArmorDetails",
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
                ("rating", models.PositiveIntegerField(default=0)),
                ("dexterity_penalty", models.IntegerField(default=0)),
                ("is_shield", models.BooleanField(default=False)),
                ("shield_bonus", models.PositiveIntegerField(default=0)),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="armor_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="AmmunitionDetails",
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
                ("caliber", models.CharField(max_length=50)),
                ("damage_modifier", models.CharField(max_length=50)),
                ("special_effects", models.TextField(blank=True)),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ammo_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="AircraftDetails",
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
                ("safe_speed", models.CharField(blank=True, max_length=100)),
                ("max_speed", models.CharField(blank=True, max_length=100)),
                ("maneuver", models.PositiveIntegerField(blank=True, null=True)),
                ("crew", models.CharField(blank=True, max_length=100)),
                ("durability", models.PositiveIntegerField(blank=True, null=True)),
                ("structure", models.PositiveIntegerField(blank=True, null=True)),
                ("weapons", models.CharField(blank=True, max_length=100)),
                ("requires_skill", models.CharField(default="Drive", max_length=100)),
                (
                    "aircraft_type",
                    models.CharField(
                        choices=[
                            ("balloon", "Hot Air Balloon"),
                            ("helicopter", "Helicopter"),
                            ("prop_plane", "Propeller Plane"),
                            ("jet", "Jet"),
                            ("fighter", "Fighter Jet"),
                            ("other", "Other"),
                        ],
                        max_length=50,
                    ),
                ),
                ("requires_specialty", models.BooleanField(default=False)),
                ("specialty_type", models.CharField(blank=True, max_length=50)),
                ("passenger_protection", models.BooleanField(default=True)),
                (
                    "equipment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="aircraft_details",
                        to="equipment.equipment",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
