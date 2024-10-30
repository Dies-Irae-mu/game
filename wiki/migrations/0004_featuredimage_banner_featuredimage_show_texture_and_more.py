# Generated by Django 4.2.13 on 2024-10-27 01:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wiki", "0003_featuredimage"),
    ]

    operations = [
        migrations.AddField(
            model_name="featuredimage",
            name="banner",
            field=models.ImageField(
                blank=True,
                help_text="Banner image displayed below the header",
                null=True,
                upload_to="banners/",
            ),
        ),
        migrations.AddField(
            model_name="featuredimage",
            name="show_texture",
            field=models.BooleanField(
                default=True, help_text="Toggle the texture overlay on/off"
            ),
        ),
        migrations.AlterField(
            model_name="featuredimage",
            name="image",
            field=models.ImageField(
                help_text="Background image for the page header", upload_to="featured/"
            ),
        ),
    ]