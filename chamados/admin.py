from django.contrib import admin
from .models import Chamado, ChamadoHistorico, ComentarioChamado, Equipamento, Setor

admin.site.register(Setor)
admin.site.register(Equipamento)


@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'setor', 'equipamento', 'prioridade', 'status', 'aberto_por', 'data_abertura')
    list_filter = ('status', 'prioridade', 'setor')
    search_fields = ('descricao', 'equipamento__nome', 'equipamento__patrimonio', 'aberto_por__username')


@admin.register(ComentarioChamado)
class ComentarioChamadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'chamado', 'autor', 'data_criacao')
    list_filter = ('data_criacao',)
    search_fields = ('texto', 'autor__username', 'chamado__id')


@admin.register(ChamadoHistorico)
class ChamadoHistoricoAdmin(admin.ModelAdmin):
    list_display = ('id', 'chamado', 'acao', 'autor', 'criado_em')
    list_filter = ('acao', 'criado_em')
    search_fields = ('detalhe', 'autor__username', 'chamado__id')