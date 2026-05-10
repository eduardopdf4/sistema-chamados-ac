from django.db import models
from django.conf import settings
from django.utils import timezone

class Setor(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Equipamento(models.Model):
    patrimonio = models.CharField(max_length=100)
    nome = models.CharField(max_length=100)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nome} - {self.patrimonio}"


class Chamado(models.Model):

    STATUS = [
        ('ABERTO', 'Aberto'),
        ('ANALISE', 'Em análise'),
        ('ANDAMENTO', 'Em andamento'),
        ('AGUARDANDO_PECA', 'Aguardando peça'),
        ('CONCLUIDO', 'Concluído'),
        ('CANCELADO', 'Cancelado'),
    ]

    PRIORIDADE = [
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
    ]

    setor = models.ForeignKey(Setor, on_delete=models.CASCADE)
    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE)
    aberto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chamados_abertos',
        blank=True,
        null=True,
    )

    descricao = models.TextField()

    prioridade = models.CharField(
        max_length=20,
        choices=PRIORIDADE
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='ABERTO'
    )

    andamento = models.TextField(blank=True, default='')
    conclusao = models.TextField(blank=True, default='')
    data_conclusao = models.DateTimeField(blank=True, null=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    imagem = models.ImageField(
        upload_to='chamados/',
        blank=True,
        null=True
    )

    data_abertura = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.equipamento} - {self.status}"

    def registrar_conclusao_se_necessario(self) -> None:
        if self.status == 'CONCLUIDO' and self.data_conclusao is None:
            self.data_conclusao = timezone.now()
        if self.status != 'CONCLUIDO':
            self.data_conclusao = None


class ComentarioChamado(models.Model):
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comentarios_chamado',
    )
    texto = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data_criacao']

    def __str__(self):
        return f"Comentário #{self.id} ({self.autor})"


class ChamadoHistorico(models.Model):
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, related_name='historico')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='historicos_chamado')
    acao = models.CharField(max_length=60)
    detalhe = models.TextField(blank=True, default='')
    status_de = models.CharField(max_length=20, blank=True, default='')
    status_para = models.CharField(max_length=20, blank=True, default='')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em']

    def __str__(self):
        return f"Histórico #{self.id} ({self.acao})"