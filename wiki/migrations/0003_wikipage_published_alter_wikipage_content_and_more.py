# Generated by Django 4.2.13 on 2024-10-31 04:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wiki", "0002_add_featured_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="wikipage",
            name="published",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="wikipage",
            name="content",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="wikipage",
            name="slug",
            field=models.SlugField(unique=True),
        ),
        migrations.AlterField(
            model_name="wikipage",
            name="title",
            field=models.CharField(max_length=200),
        ),
    ]
