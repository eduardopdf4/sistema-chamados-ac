from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PerfilUsuario

User = get_user_model()


@receiver(post_save, sender=User)
def limpar_solicitacao_admin_ao_promover(sender, instance: User, **kwargs):
    """Quando o superusuário concede `is_staff` no Admin, encerra a pendência de aprovação."""
    if not instance.is_staff:
        return
    try:
        perfil = PerfilUsuario.objects.get(user=instance)
    except PerfilUsuario.DoesNotExist:
        return
    if perfil.solicitacao_admin_pendente:
        perfil.solicitacao_admin_pendente = False
        perfil.save(update_fields=["solicitacao_admin_pendente"])
