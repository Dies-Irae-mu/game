# Generated by Django 4.2.16 on 2025-03-19 05:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("objects", "0015_crisis_outcome_task"),
        ("typeclasses", "0016_alter_attribute_id_alter_tag_id"),
        ("groups", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CharacterGroupInfo",
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
                    "db_key",
                    models.CharField(db_index=True, max_length=255, verbose_name="key"),
                ),
                (
                    "db_typeclass_path",
                    models.CharField(
                        db_index=True,
                        help_text="this defines what 'type' of entity this is. This variable holds a Python path to a module with a valid Evennia Typeclass.",
                        max_length=255,
                        null=True,
                        verbose_name="typeclass",
                    ),
                ),
                (
                    "db_date_created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="creation date"
                    ),
                ),
                (
                    "db_lock_storage",
                    models.TextField(
                        blank=True,
                        help_text="locks limit access to an entity. A lock is defined as a 'lock string' on the form 'type:lockfunctions', defining what functionality is locked and how to determine access. Not defining a lock means no access is granted.",
                        verbose_name="locks",
                    ),
                ),
                (
                    "db_group_description",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Character's personal group information",
                    ),
                ),
                (
                    "db_faction_description",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Character's faction information",
                    ),
                ),
                (
                    "db_attributes",
                    models.ManyToManyField(
                        help_text="attributes on this object. An attribute can hold any pickle-able python object (see docs for special cases).",
                        to="typeclasses.attribute",
                    ),
                ),
                (
                    "db_character",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="group_info",
                        to="objects.objectdb",
                    ),
                ),
                (
                    "db_tags",
                    models.ManyToManyField(
                        help_text="tags on this object. Tags are simple string markers to identify, group and alias objects.",
                        to="typeclasses.tag",
                    ),
                ),
            ],
            options={
                "verbose_name": "Character Group Info",
                "verbose_name_plural": "Character Group Data",
            },
        ),
        migrations.DeleteModel(
            name="GroupInfo",
        ),
    ]
