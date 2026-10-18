from django.apps import AppConfig


class StaffsConfig(AppConfig):
    name = 'staffs'

    def ready(self):
        import staffs.signals
