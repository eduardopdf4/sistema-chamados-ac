from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Chamado,
    ChamadoHistorico,
    ComentarioChamado,
    Equipamento,
    Notificacao,
    PerfilUsuario,
    Setor,
)

User = get_user_model()


class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    extra = 0
    fields = (
        "nome_completo",
        "setor",
        "solicitacao_admin_pendente",
    )


class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)
    list_display = (
        "username",
        "email",
        "is_staff",
        "is_superuser",
        "is_active",
    )

    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
    )


try:
    admin.site.unregister(User)
except NotRegistered:
    pass

admin.site.register(User, UserAdmin)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = (
        "nome_completo",
        "user",
        "setor",
        "solicitacao_admin_pendente",
    )

    list_filter = (
        "solicitacao_admin_pendente",
    )

    search_fields = (
        "nome_completo",
        "setor",
        "user__username",
        "user__email",
    )


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "titulo",
        "destinatario",
        "tipo",
        "lida",
        "criada_em",
        "chamado",
    )

    list_filter = (
        "lida",
        "tipo",
        "criada_em",
    )

    search_fields = (
        "titulo",
        "mensagem",
        "destinatario__username",
    )


admin.site.register(Setor)
admin.site.register(Equipamento)


@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nome_solicitante",
        "setor_local",
        "tipo_chamado",
        "prioridade",
        "status",
        "aberto_por",
        "data_abertura",
    )

    list_filter = (
        "status",
        "prioridade",
        "setor_local",
        "tipo_chamado",
    )

    search_fields = (
        "nome_solicitante",
        "descricao",
        "setor_local",
        "tipo_chamado",
        "aberto_por__username",
        "aberto_por__email",
    )

    readonly_fields = (
        "data_abertura",
        "atualizado_em",
        "data_conclusao",
    )


@admin.register(ComentarioChamado)
class ComentarioChamadoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "chamado",
        "autor",
        "data_criacao",
    )

    list_filter = (
        "data_criacao",
    )

    search_fields = (
        "texto",
        "autor__username",
        "chamado__id",
    )


@admin.register(ChamadoHistorico)
class ChamadoHistoricoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "chamado",
        "acao",
        "autor",
        "criado_em",
    )

    list_filter = (
        "acao",
        "criado_em",
    )

    search_fields = (
        "detalhe",
        "autor__username",
        "chamado__id",
    )