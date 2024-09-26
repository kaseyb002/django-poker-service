from django.apps import AppConfig


class PokerappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pokerapp'

    def ready(self):
        import pokerapp.signals 
