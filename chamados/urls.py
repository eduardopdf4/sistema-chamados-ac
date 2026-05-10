from django.urls import path

from . import views


app_name = 'chamados'

urlpatterns = [
    path('', views.meus_chamados, name='meus_chamados'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('novo/', views.novo_chamado, name='novo_chamado'),
    path('chamado/<int:pk>/', views.detalhe_chamado, name='detalhe_chamado'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('sair/', views.LogoutView.as_view(), name='logout'),
]

