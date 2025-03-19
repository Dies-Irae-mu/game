from django.apps import AppConfig

class GroupsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'world.groups'

    def ready(self):
        import world.groups.signals