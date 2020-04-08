from django.apps import AppConfig


class ScholarConfig(AppConfig):
    name = 'apps.scholar'

    def ready(self):
        import apps.scholar.signals
        # import apps.scholar.modules.strategy
