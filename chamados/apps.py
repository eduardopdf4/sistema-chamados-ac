from django.apps import AppConfig


class ChamadosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chamados"
    verbose_name = "Chamados ACQUA"

    def ready(self) -> None:
        from . import signals  # noqa: F401
