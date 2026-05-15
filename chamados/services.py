from __future__ import annotations

from typing import Iterable

from django.contrib.auth import get_user_model

from .models import Notificacao

User = get_user_model()


def criar_notificacoes(
    destinatarios: Iterable[User],
    titulo: str,
    mensagem: str,
    *,
    tipo: str,
    chamado=None,
    excluir_user_ids: set[int] | None = None,
) -> int:
    """Cria notificações em lote. Retorna quantidade criada."""
    excluir = excluir_user_ids or set()
    objs = [
        Notificacao(
            destinatario=u,
            titulo=titulo[:200],
            mensagem=mensagem,
            tipo=tipo,
            chamado=chamado,
        )
        for u in destinatarios
        if u.is_active and u.id not in excluir
    ]
    if not objs:
        return 0
    Notificacao.objects.bulk_create(objs, batch_size=200)
    return len(objs)


def usuarios_staff_ativos():
    return User.objects.filter(is_active=True, is_staff=True)
