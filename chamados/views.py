from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ChamadoForm, ChamadoStatusForm
from .models import Chamado, ChamadoHistorico, ComentarioChamado


class LoginView(LoginView):
    template_name = 'chamados/login.html'


class LogoutView(LogoutView):
    next_page = 'chamados:login'


@login_required
def meus_chamados(request: HttpRequest) -> HttpResponse:
    chamados = (
        Chamado.objects.filter(aberto_por=request.user)
        .select_related('setor', 'equipamento')
        .order_by('-data_abertura')
    )
    return render(request, 'chamados/meus_chamados.html', {'chamados': chamados})


@login_required
def novo_chamado(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = ChamadoForm(request.POST, request.FILES)
        if form.is_valid():
            chamado = form.save(commit=False)
            chamado.aberto_por = request.user
            chamado.save()
            ChamadoHistorico.objects.create(
                chamado=chamado,
                autor=request.user,
                acao='ABERTURA',
                detalhe='Chamado aberto pelo colaborador.',
                status_para=chamado.status,
            )
            return redirect('chamados:meus_chamados')
    else:
        form = ChamadoForm()

    return render(request, 'chamados/novo_chamado.html', {'form': form})


@user_passes_test(lambda u: u.is_active and u.is_superuser)
def dashboard(request: HttpRequest) -> HttpResponse:
    chamados = (
        Chamado.objects.all()
        .select_related('setor', 'equipamento', 'aberto_por')
        .order_by('-data_abertura')
    )
    return render(request, 'chamados/dashboard.html', {'chamados': chamados})


@login_required
def detalhe_chamado(request: HttpRequest, pk: int) -> HttpResponse:
    chamado = get_object_or_404(
        Chamado.objects.select_related('setor', 'equipamento', 'aberto_por'),
        pk=pk,
    )

    pode_gerenciar = request.user.is_staff
    if not pode_gerenciar and chamado.aberto_por_id != request.user.id:
        return redirect('chamados:meus_chamados')

    status_form = ChamadoStatusForm(instance=chamado)

    if request.method == 'POST' and pode_gerenciar and 'salvar_atualizacao' in request.POST:
        status_form = ChamadoStatusForm(request.POST, instance=chamado)
        texto_comentario = request.POST.get('texto_comentario', '').strip()

        if status_form.is_valid():
            status_antes = chamado.status
            chamado = status_form.save(commit=False)
            chamado.registrar_conclusao_se_necessario()
            chamado.save()

            if status_antes != chamado.status:
                ChamadoHistorico.objects.create(
                    chamado=chamado,
                    autor=request.user,
                    acao='STATUS',
                    detalhe='Status atualizado.',
                    status_de=status_antes,
                    status_para=chamado.status,
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
                    acao='COMENTARIO',
                    detalhe='Comentário da engenharia/admin.',
                    status_para=chamado.status,
                )

            return redirect('chamados:detalhe_chamado', pk=chamado.pk)

    comentarios = chamado.comentarios.select_related('autor').order_by('data_criacao')

    return render(
        request,
        'chamados/detalhe_chamado.html',
        {
            'chamado': chamado,
            'pode_gerenciar': pode_gerenciar,
            'status_form': status_form,
            'comentarios': comentarios,
        },
    )
