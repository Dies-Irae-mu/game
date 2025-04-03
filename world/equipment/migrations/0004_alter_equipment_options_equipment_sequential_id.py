# Generated by Django 4.2.16 on 2025-03-31 04:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("equipment", "0003_aircraft_ammunition_artifact_biotech_chimerical_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="equipment",
            options={"ordering": ["sequential_id"]},
        ),
        migrations.AddField(
            model_name="equipment",
            name="sequential_id",
            field=models.PositiveIntegerField(blank=True, null=True, unique=True),
        ),
    ]
