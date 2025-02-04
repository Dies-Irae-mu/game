# Generated by Django 4.2.16 on 2025-02-03 07:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wod20th", "0016_alter_stat_stat_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="stat",
            name="breed",
            field=models.CharField(
                blank=True,
                choices=[
                    ("homid", "Homid"),
                    ("metis", "Metis"),
                    ("lupus", "Lupus"),
                    ("feline", "Feline"),
                    ("squamus", "Squamus"),
                    ("ursine", "Ursine"),
                    ("latrani", "Latrani"),
                    ("rodens", "Rodens"),
                    ("corvid", "Corvid"),
                    ("balaram", "Balaram"),
                    ("suchid", "Suchid"),
                    ("ahi", "Ahi"),
                    ("arachnid", "Arachnid"),
                    ("kojin", "Kojin"),
                    ("roko", "Roko"),
                    ("shinju", "Shinju"),
                    ("animal-born", "Animal-Born"),
                    ("none", "None"),
                ],
                default="none",
                max_length=100,
            ),
        ),
    ]
