from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CadastroUsuarioForm, ChamadoForm, ChamadoStatusForm, DashboardFiltroForm
from .models import Chamado, ChamadoHistorico, ComentarioChamado, Notificacao
from .services import criar_notificacoes, usuarios_staff_ativos


def _inicio_fim_dia(d: date) -> tuple[datetime, datetime]:
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(d, time.min), tz)
    end = timezone.make_aware(datetime.combine(d, time.max), tz)
    return start, end


class LoginView(DjangoLoginView):
    template_name = "chamados/login.html"
    redirect_authenticated_user = True


class LogoutView(DjangoLogoutView):
    next_page = "chamados:login"


def cadastro_usuario(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("chamados:meus_chamados")

    if request.method == "POST":
        form = CadastroUsuarioForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Cadastro realizado com sucesso. Faça login com seu e-mail e senha.")

            if form.cleaned_data["tipo_conta"] == CadastroUsuarioForm.TIPO_ADMIN:
                messages.info(
                    request,
                    'Você solicitou perfil de administrador. Um superusuário precisará aprovar em /admin/ '
                    'marcando "Usuário staff" / is_staff antes que o acesso administrativo seja liberado.',
                )

            return redirect("chamados:login")
    else:
        form = CadastroUsuarioForm()

    return render(request, "chamados/cadastro.html", {"form": form})


@login_required
def meus_chamados(request: HttpRequest) -> HttpResponse:
    chamados = (
        Chamado.objects.filter(aberto_por=request.user)
        .order_by("-data_abertura")
    )

    return render(request, "chamados/meus_chamados.html", {"chamados": chamados})


@login_required
def novo_chamado(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ChamadoForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            chamado = form.save(commit=False)
            chamado.aberto_por = request.user

            if not chamado.nome_solicitante:
                if hasattr(request.user, "perfil") and request.user.perfil.nome_completo:
                    chamado.nome_solicitante = request.user.perfil.nome_completo
                else:
                    chamado.nome_solicitante = request.user.get_full_name() or request.user.username

            chamado.save()

            ChamadoHistorico.objects.create(
                chamado=chamado,
                autor=request.user,
                acao="ABERTURA",
                detalhe="Chamado de manutenção aberto pelo solicitante.",
                status_para=chamado.status,
            )

            criar_notificacoes(
                list(usuarios_staff_ativos()),
                titulo=f"Novo chamado #{chamado.pk}",
                mensagem=f"{chamado.nome_solicitante} abriu um novo chamado de manutenção.",
                tipo=Notificacao.TIPO_NOVO_CHAMADO,
                chamado=chamado,
                excluir_user_ids={request.user.id},
            )

            messages.success(request, "Chamado registrado com sucesso.")
            return redirect("chamados:meus_chamados")
    else:
        form = ChamadoForm(user=request.user)

    return render(request, "chamados/novo_chamado.html", {"form": form})


def _filtrar_chamados_dashboard(qs, filtro: DashboardFiltroForm) -> Any:
    if not filtro.is_valid():
        return qs

    data = filtro.cleaned_data

    if data.get("setor_local"):
        qs = qs.filter(setor_local=data["setor_local"])

    if data.get("status"):
        qs = qs.filter(status=data["status"])

    if data.get("prioridade"):
        qs = qs.filter(prioridade=data["prioridade"])

    if data.get("data_inicio"):
        start, _ = _inicio_fim_dia(data["data_inicio"])
        qs = qs.filter(data_abertura__gte=start)

    if data.get("data_fim"):
        _, end = _inicio_fim_dia(data["data_fim"])
        qs = qs.filter(data_abertura__lte=end)

    return qs


@user_passes_test(lambda u: u.is_active and u.is_staff)
def dashboard(request: HttpRequest) -> HttpResponse:
    filtro_form = DashboardFiltroForm(request.GET or None)

    base = Chamado.objects.all().select_related("aberto_por")
    qs = _filtrar_chamados_dashboard(base, filtro_form)
    chamados = qs.order_by("-data_abertura")

    total = qs.count()
    contagem_status = {
        row["status"]: row["c"]
        for row in qs.values("status").annotate(c=Count("id"))
    }

    def cnt(st: str) -> int:
        return int(contagem_status.get(st, 0))

    prioridade_rows = list(
        qs.values("prioridade").annotate(c=Count("id")).order_by("prioridade")
    )

    recentes = list(chamados[:12])

    context = {
        "chamados": chamados,
        "filtro_form": filtro_form,
        "kpi_total": total,
        "kpi_aberto": cnt("ABERTO") + cnt("ANALISE"),
        "kpi_andamento": cnt("ANDAMENTO") + cnt("AGUARDANDO"),
        "kpi_concluido": cnt("CONCLUIDO"),
        "kpi_cancelado": cnt("CANCELADO"),
        "prioridade_rows": prioridade_rows,
        "recentes": recentes,
    }

    return render(request, "chamados/dashboard.html", context)


@login_required
def detalhe_chamado(request: HttpRequest, pk: int) -> HttpResponse:
    chamado = get_object_or_404(
        Chamado.objects.select_related("aberto_por"),
        pk=pk,
    )

    pode_gerenciar = request.user.is_staff

    if not pode_gerenciar and chamado.aberto_por_id != request.user.id:
        messages.warning(request, "Você não tem permissão para acessar este chamado.")
        return redirect("chamados:meus_chamados")

    status_form = ChamadoStatusForm(instance=chamado)

    if request.method == "POST":
        if pode_gerenciar and "salvar_atualizacao" in request.POST:
            status_form = ChamadoStatusForm(request.POST, instance=chamado)
            texto_comentario = request.POST.get("texto_comentario", "").strip()

            if status_form.is_valid():
                status_antes = chamado.status
                chamado = status_form.save(commit=False)
                chamado.registrar_conclusao_se_necessario()
                chamado.save()

                destinatarios = []

                if chamado.aberto_por and chamado.aberto_por.id != request.user.id:
                    destinatarios.append(chamado.aberto_por)

                for admin_user in usuarios_staff_ativos():
                    if admin_user.id != request.user.id and admin_user not in destinatarios:
                        destinatarios.append(admin_user)

                if status_antes != chamado.status:
                    ChamadoHistorico.objects.create(
                        chamado=chamado,
                        autor=request.user,
                        acao="STATUS",
                        detalhe="Status atualizado pela equipe de manutenção.",
                        status_de=status_antes,
                        status_para=chamado.status,
                    )

                    criar_notificacoes(
                        destinatarios,
                        titulo=f"Chamado #{chamado.pk} - status atualizado",
                        mensagem=(
                            f'O status passou de "{dict(Chamado.STATUS).get(status_antes, status_antes)}" '
                            f'para "{chamado.get_status_display()}".'
                        ),
                        tipo=Notificacao.TIPO_STATUS,
                        chamado=chamado,
                    )

                if texto_comentario:
                    ComentarioChamado.objects.create(
                        chamado=chamado,
                        autor=request.user,
                        texto=texto_comentario,
                    )

                    ChamadoHistorico.objects.create(
                        chamado=chamado,
                        autor=request.user,
                        acao="COMENTARIO",
                        detalhe="Comentário da equipe / administrador.",
                        status_para=chamado.status,
                    )

                    criar_notificacoes(
                        destinatarios,
                        titulo=f"Novo comentário no chamado #{chamado.pk}",
                        mensagem="Foi registrado um novo comentário no chamado.",
                        tipo=Notificacao.TIPO_COMENTARIO_ADMIN,
                        chamado=chamado,
                    )

                messages.success(request, "Atualização salva.")
                return redirect("chamados:detalhe_chamado", pk=chamado.pk)

        elif "enviar_comentario_solicitante" in request.POST and chamado.aberto_por_id == request.user.id:
            texto = request.POST.get("texto_solicitante", "").strip()

            if texto:
                ComentarioChamado.objects.create(
                    chamado=chamado,
                    autor=request.user,
                    texto=texto,
                )

                ChamadoHistorico.objects.create(
                    chamado=chamado,
                    autor=request.user,
                    acao="COMENTARIO_SOLICITANTE",
                    detalhe="Comentário do solicitante.",
                    status_para=chamado.status,
                )

                criar_notificacoes(
                    list(usuarios_staff_ativos()),
                    titulo=f"Novo comentário no chamado #{chamado.pk}",
                    mensagem=f"{request.user.get_username()} comentou no chamado.",
                    tipo=Notificacao.TIPO_COMENTARIO_COLAB,
                    chamado=chamado,
                    excluir_user_ids={request.user.id},
                )

                messages.success(request, "Comentário enviado.")
            else:
                messages.error(request, "Digite uma mensagem antes de enviar.")

            return redirect("chamados:detalhe_chamado", pk=chamado.pk)

    comentarios = chamado.comentarios.select_related("autor").order_by("data_criacao")
    historico = chamado.historico.select_related("autor").order_by("-criado_em")

    return render(
        request,
        "chamados/detalhe_chamado.html",
        {
            "chamado": chamado,
            "pode_gerenciar": pode_gerenciar,
            "status_form": status_form,
            "comentarios": comentarios,
            "historico": historico,
        },
    )


@login_required
def minhas_notificacoes(request: HttpRequest) -> HttpResponse:
    lista = (
        Notificacao.objects.filter(destinatario=request.user)
        .select_related("chamado")
        .order_by("-criada_em")[:200]
    )

    if request.method == "POST" and request.POST.get("marcar_todas_lidas"):
        Notificacao.objects.filter(destinatario=request.user, lida=False).update(lida=True)
        messages.success(request, "Todas as notificações foram marcadas como lidas.")
        return redirect("chamados:notificacoes")

    return render(request, "chamados/notificacoes.html", {"notificacoes": lista})


@login_required
def marcar_notificacao_lida(request: HttpRequest, pk: int) -> HttpResponse:
    notif = get_object_or_404(Notificacao, pk=pk, destinatario=request.user)
    notif.lida = True
    notif.save(update_fields=["lida"])

    if notif.chamado_id:
        return redirect("chamados:detalhe_chamado", pk=notif.chamado_id)

    return redirect("chamados:notificacoes")