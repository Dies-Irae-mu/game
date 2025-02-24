from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('wod20th', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='stat',
            name='gift_alias',
            field=models.JSONField(
                default=list,
                blank=True,
                null=True,
                help_text="List of alternative names for this gift"
            ),
        ),
    ] 