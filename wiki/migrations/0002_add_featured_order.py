from django.db import migrations, models

def remove_duplicates(apps, schema_editor):
    WikiPage = apps.get_model('wiki', 'WikiPage')
    
    # Get all titles and their counts
    from django.db.models import Count
    duplicates = WikiPage.objects.values('title').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    # For each set of duplicates, keep the first one and modify others
    for dup in duplicates:
        title = dup['title']
        pages = WikiPage.objects.filter(title=title).order_by('created_at')
        
        # Skip the first one (keep it as is)
        first = True
        for page in pages:
            if first:
                first = False
                continue
            
            # Modify duplicate titles by adding a suffix
            counter = 1
            new_title = f"{title} ({counter})"
            while WikiPage.objects.filter(title=new_title).exists():
                counter += 1
                new_title = f"{title} ({counter})"
            
            page.title = new_title
            page.save()

class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0001_initial'),
    ]

    operations = [
        # First remove any duplicates
        migrations.RunPython(remove_duplicates),
        
        # Then add the featured_order field
        migrations.AddField(
            model_name='wikipage',
            name='featured_order',
            field=models.IntegerField(default=0),
        ),
    ] 