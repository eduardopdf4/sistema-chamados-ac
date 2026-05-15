from django.urls import path
from . import views

app_name = "chamados"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("cadastro/", views.cadastro_usuario, name="cadastro"),

    path("novo/", views.novo_chamado, name="novo_chamado"),
    path("meus/", views.meus_chamados, name="meus_chamados"),

    path("chamado/<int:pk>/", views.detalhe_chamado, name="detalhe_chamado"),

    path("notificacoes/", views.minhas_notificacoes, name="notificacoes"),
    path(
        "notificacoes/<int:pk>/lida/",
        views.marcar_notificacao_lida,
        name="marcar_notificacao_lida",
    ),
]