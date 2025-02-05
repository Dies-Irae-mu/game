# Generated by Django 4.2.16 on 2025-01-19 23:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("objects", "0015_crisis_outcome_task"),
        ("wod20th", "0009_stat_notes_alter_stat_stat_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="CharacterImage",
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
                ("image", models.ImageField(upload_to="character_images/")),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("is_primary", models.BooleanField(default=False)),
                (
                    "character",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="objects.objectdb",
                    ),
                ),
            ],
            options={
                "ordering": ["-is_primary", "-uploaded_at"],
            },
        ),
    ]
