from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0001_initial'),  # Adjust this to depend on your latest migration
    ]

    operations = [
        migrations.AlterModelOptions(
            name='wikipage',
            options={
                'permissions': [
                    ('can_upload_images', 'Can upload images to wiki pages'),
                ],
            },
        ),
    ] 