# Generated by Django 4.2.16 on 2024-10-17 22:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0002_archivedjob"),
    ]

    operations = [
        migrations.AlterField(
            model_name="job",
            name="status",
            field=models.CharField(
                choices=[
                    ("open", "Open"),
                    ("claimed", "Claimed"),
                    ("closed", "Closed"),
                    ("rejected", "Rejected"),
                    ("cancelled", "Cancelled"),
                    ("completed", "Completed"),
                ],
                default="open",
                max_length=20,
            ),
        ),
    ]
