from django.apps import AppConfig


class InspectionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inspections'
    verbose_name = 'Vehicle Inspections'
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            import inspections.signals
        except ImportError:
            pass