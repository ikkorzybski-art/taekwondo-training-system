from django.apps import AppConfig

class TrainingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'training'
    verbose_name = 'System Treningów Taekwon-Do'
    
    def ready(self):
        import training.models  # Ładowanie sygnałów