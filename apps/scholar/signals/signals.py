from django.dispatch import Signal

serializer_created = Signal(providing_args=["instance"])

