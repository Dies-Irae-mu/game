"""
Reset sequence for hangouts table to start from 1.
"""
from django.db import migrations

def reset_sequence(apps, schema_editor):
    """Reset the sequence for hangouts table to start from 1."""
    if schema_editor.connection.vendor == 'postgresql':
        # For PostgreSQL
        schema_editor.execute("ALTER SEQUENCE objects_id_seq RESTART WITH 1;")
    elif schema_editor.connection.vendor == 'sqlite3':
        # For SQLite
        schema_editor.execute("DELETE FROM sqlite_sequence WHERE name='objects';")
        schema_editor.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('objects', 0);")

class Migration(migrations.Migration):
    dependencies = [
        ('hangouts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(reset_sequence),
    ]