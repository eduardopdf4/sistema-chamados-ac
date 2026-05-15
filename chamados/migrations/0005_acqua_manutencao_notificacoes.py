# Generated manually for CHAMADOS ACQUA — manutenção geral, perfis e notificações

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def criar_perfis_usuarios(apps, schema_editor):
    User = apps.get_model("auth", "User")
    PerfilUsuario = apps.get_model("chamados", "PerfilUsuario")
    for u in User.objects.all():
        if PerfilUsuario.objects.filter(user_id=u.pk).exists():
            continue
        nome = f"{u.first_name} {u.last_name}".strip() or u.username
        PerfilUsuario.objects.create(
            user_id=u.pk,
            nome_completo=(nome or "Usuário")[:200],
            setor="(não informado no cadastro legado)",
            solicitacao_admin_pendente=False,
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("chamados", "0004_comentariochamado_rename"),
    ]

    operations = [
        migrations.CreateModel(
            name="PerfilUsuario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome_completo", models.CharField(max_length=200)),
                ("setor", models.CharField(help_text="Setor de lotação do colaborador.", max_length=150)),
                (
                    "solicitacao_admin_pendente",
                    models.BooleanField(
                        default=False,
                        help_text="True quando o cadastro pediu perfil administrador e ainda não foi aprovado.",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="perfil",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Perfil de usuário",
                "verbose_name_plural": "Perfis de usuários",
            },
        ),
        migrations.CreateModel(
            name="Notificacao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=200)),
                ("mensagem", models.TextField(blank=True, default="")),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("NOVO_CHAMADO", "Novo chamado"),
                            ("STATUS", "Alteração de status"),
                            ("COMENTARIO_ADMIN", "Comentário da equipe"),
                            ("COMENTARIO_COLAB", "Comentário do solicitante"),
                        ],
                        default="STATUS",
                        max_length=30,
                    ),
                ),
                ("lida", models.BooleanField(default=False)),
                ("criada_em", models.DateTimeField(auto_now_add=True)),
                (
                    "chamado",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notificacoes",
                        to="chamados.chamado",
                    ),
                ),
                (
                    "destinatario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notificacoes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-criada_em"],
                "verbose_name": "Notificação",
                "verbose_name_plural": "Notificações",
            },
        ),
        migrations.AddField(
            model_name="chamado",
            name="anexo",
            field=models.FileField(
                blank=True,
                help_text="Arquivo complementar (PDF, imagem, etc.).",
                null=True,
                upload_to="chamados/anexos/",
            ),
        ),
        migrations.AddField(
            model_name="chamado",
            name="local_intervencao",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Local físico onde a intervenção é necessária.",
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name="chamado",
            name="tipo_intervencao",
            field=models.CharField(
                choices=[
                    ("PREVENTIVA", "Preventiva"),
                    ("CORRETIVA", "Corretiva"),
                    ("PREDITIVA", "Preditiva"),
                    ("INSTALACAO", "Instalação / adequação"),
                    ("INSPECAO", "Inspeção / vistoria"),
                    ("OUTRA", "Outra"),
                ],
                default="OUTRA",
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="chamado",
            name="descricao",
            field=models.TextField(verbose_name="Descrição do problema"),
        ),
        migrations.AlterField(
            model_name="chamado",
            name="equipamento",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="chamados",
                to="chamados.equipamento",
            ),
        ),
        migrations.RunPython(criar_perfis_usuarios, noop_reverse),
    ]
