# Generated by Django 4.2.16 on 2025-03-19 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("groups", "0002_charactergroupinfo_delete_groupinfo"),
    ]

    operations = [
        migrations.AddField(
            model_name="group",
            name="notes",
            field=models.TextField(
                blank=True,
                help_text="Private notes visible only to staff and group members",
            ),
        ),
    ]
