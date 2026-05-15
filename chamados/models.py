from django.conf import settings
from django.db import models
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


class PerfilUsuario(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
    )
    nome_completo = models.CharField(max_length=200)
    setor = models.CharField(max_length=150)
    solicitacao_admin_pendente = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Perfil de usuário"
        verbose_name_plural = "Perfis de usuários"

    def __str__(self):
        return f"{self.nome_completo} ({self.user.email or self.user.username})"


class Notificacao(models.Model):
    TIPO_NOVO_CHAMADO = "NOVO_CHAMADO"
    TIPO_STATUS = "STATUS"
    TIPO_COMENTARIO_ADMIN = "COMENTARIO_ADMIN"
    TIPO_COMENTARIO_COLAB = "COMENTARIO_COLAB"

    TIPOS = [
        (TIPO_NOVO_CHAMADO, "Novo chamado"),
        (TIPO_STATUS, "Alteração de status"),
        (TIPO_COMENTARIO_ADMIN, "Comentário da equipe"),
        (TIPO_COMENTARIO_COLAB, "Comentário do solicitante"),
    ]

    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificacoes",
    )
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField(blank=True, default="")
    chamado = models.ForeignKey(
        "Chamado",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notificacoes",
    )
    tipo = models.CharField(max_length=30, choices=TIPOS, default=TIPO_STATUS)
    lida = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criada_em"]
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"

    def __str__(self):
        return f"{self.titulo} - {self.destinatario}"


class Chamado(models.Model):
    STATUS = [
        ("ABERTO", "Aberto"),
        ("ANALISE", "Em análise"),
        ("ANDAMENTO", "Em andamento"),
        ("AGUARDANDO", "Aguardando atendimento"),
        ("CONCLUIDO", "Concluído"),
        ("CANCELADO", "Cancelado"),
    ]

    PRIORIDADE = [
        ("BAIXA", "Baixa"),
        ("MEDIA", "Média"),
        ("ALTA", "Alta"),
        ("URGENTE", "Urgente"),
    ]

    SETOR_LOCAL = [
        ("RECEPCAO_1", "RECEPÇÃO 1"),
        ("RECEPCAO_2", "RECEPÇÃO 2"),
        ("SALA_ATENDIMENTO", "SALA DE ATENDIMENTO"),
        ("BANHEIRO_RECEPCAO", "BANHEIRO DA RECEPÇÃO"),
        ("DIRECAO_EXECUTIVA", "SALA DA DIREÇÃO EXECUTIVA"),
        ("DIRECAO_ADJUNTA_GERENCIA", "SALA DA DIREÇÃO ADJUNTA/GERÊNCIA"),
        ("SUPERVISAO_TECNICA", "SALA DA SUPERVISÃO TÉCNICA"),
        ("COMUNICACAO", "SALA DA COMUNICAÇÃO"),
        ("CONTROLADORIA", "SALA DA CONTROLADORIA"),
        ("ORCAMENTO_FARMACIA", "SALA DO ORÇAMENTO/FARMÁCIA"),
        ("PRESTACAO_CONTAS", "SALA DA PRESTAÇÃO DE CONTAS"),
        ("SALA_REUNIAO", "SALA DE REUNIÃO"),
        ("JURIDICO", "SALA DO JURÍDICO"),
        ("CONFERENCIA", "SALA DE CONFERÊNCIA"),
        ("ENGENHARIA", "SALA DA ENGENHARIA"),
        ("FINANCEIRO", "SALA DO FINANCEIRO"),
        ("QUALIDADE", "SALA DA QUALIDADE"),
        ("RH", "SALA DO RH"),
        ("AREA_VIVENCIA", "ÁREA DE VIVÊNCIA"),
        ("AREA_CONDENSADORAS", "ÁREA DAS CONDENSADORAS"),
        ("DML", "SALA DO DML"),
        ("COPA", "COPA"),
        ("BANHEIRO_FEMININO", "BANHEIRO FEMININO"),
        ("BANHEIRO_MASCULINO", "BANHEIRO MASCULINO"),
    ]

    TIPO_CHAMADO = [
        ("INFRAESTRUTURA", "INFRAESTRUTURA PREDIAL"),
        ("CLIMATIZACAO", "CLIMATIZAÇÃO"),
        ("ELETRICA", "ELÉTRICA"),
        ("HIDRAULICA", "HIDRÁULICA"),
        ("MOBILIARIO", "MOBILIÁRIO"),
        ("EQUIPAMENTO_PATRIMONIO", "EQUIPAMENTO/PATRIMÔNIO"),
        ("LIMPEZA_ORGANIZACAO", "LIMPEZA/ORGANIZAÇÃO"),
        ("SEGURANCA_PREDIAL", "SEGURANÇA PREDIAL"),
        ("OUTROS_ENGENHARIA", "OUTROS SERVIÇOS DE ENGENHARIA"),
    ]

    aberto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chamados_abertos",
        blank=True,
        null=True,
    )

    nome_solicitante = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Nome do solicitante",
    )

    setor_local = models.CharField(
        max_length=80,
        choices=SETOR_LOCAL,
        verbose_name="Setor / Local da solicitação",
    )

    tipo_chamado = models.CharField(
        max_length=80,
        choices=TIPO_CHAMADO,
        verbose_name="Tipo de chamado",
    )

    descricao = models.TextField(verbose_name="Descrição do problema")

    prioridade = models.CharField(
        max_length=20,
        choices=PRIORIDADE,
        verbose_name="Prioridade",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="ABERTO",
        verbose_name="Status",
    )

    andamento = models.TextField(blank=True, default="")
    conclusao = models.TextField(blank=True, default="")
    data_conclusao = models.DateTimeField(blank=True, null=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    imagem = models.ImageField(
        upload_to="chamados/",
        blank=True,
        null=True,
        verbose_name="Imagem do problema",
    )

    data_abertura = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_setor_local_display()} - {self.get_tipo_chamado_display()} - {self.get_status_display()}"

    def registrar_conclusao_se_necessario(self) -> None:
        if self.status == "CONCLUIDO" and self.data_conclusao is None:
            self.data_conclusao = timezone.now()
        if self.status != "CONCLUIDO":
            self.data_conclusao = None


class ComentarioChamado(models.Model):
    chamado = models.ForeignKey(
        Chamado,
        on_delete=models.CASCADE,
        related_name="comentarios",
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comentarios_chamado",
    )
    texto = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["data_criacao"]

    def __str__(self):
        return f"Comentário #{self.id} ({self.autor})"


class ChamadoHistorico(models.Model):
    chamado = models.ForeignKey(
        Chamado,
        on_delete=models.CASCADE,
        related_name="historico",
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="historicos_chamado",
    )
    acao = models.CharField(max_length=60)
    detalhe = models.TextField(blank=True, default="")
    status_de = models.CharField(max_length=20, blank=True, default="")
    status_para = models.CharField(max_length=20, blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["criado_em"]

    def __str__(self):
        return f"Histórico #{self.id} ({self.acao})"