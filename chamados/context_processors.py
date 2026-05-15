from .models import Notificacao


def notificacoes_nao_lidas(request):
    if not request.user.is_authenticated:
        return {"notificacoes_nao_lidas_count": 0}

    count = Notificacao.objects.filter(
        destinatario=request.user,
        lida=False
    ).count()

    return {"notificacoes_nao_lidas_count": count}