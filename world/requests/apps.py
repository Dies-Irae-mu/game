from django.apps import AppConfig

class MailConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'world.requests'

    def ready(self):
        import world.requests.signals