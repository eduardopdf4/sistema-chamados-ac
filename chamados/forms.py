from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import Chamado, PerfilUsuario

User = get_user_model()


class CadastroUsuarioForm(forms.Form):
    TIPO_COLAB = "COLAB"
    TIPO_ADMIN = "ADMIN"

    nome_completo = forms.CharField(
        label="Nome completo",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "name"}),
    )

    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
    )

    setor = forms.ChoiceField(
        label="Setor",
        choices=Chamado.SETOR_LOCAL,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    password1 = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    password2 = forms.CharField(
        label="Confirmação de senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    tipo_conta = forms.ChoiceField(
        label="Tipo de conta",
        choices=[
            (TIPO_COLAB, "Colaborador"),
            (TIPO_ADMIN, "Administrador (sujeito à aprovação do superusuário)"),
        ],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        initial=TIPO_COLAB,
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(username__iexact=email).exists():
            raise ValidationError("Este e-mail já está cadastrado.")

        return email

    def clean(self):
        data = super().clean()
        p1 = data.get("password1")
        p2 = data.get("password2")

        if p1 and p2 and p1 != p2:
            self.add_error("password2", "As senhas não conferem.")

        return data

    def save(self):
        data = self.cleaned_data
        email = data["email"]

        user = User.objects.create_user(
            username=email,
            email=email,
            password=data["password1"],
            is_staff=False,
            is_superuser=False,
        )

        PerfilUsuario.objects.create(
            user=user,
            nome_completo=data["nome_completo"].strip(),
            setor=data["setor"],
            solicitacao_admin_pendente=(data["tipo_conta"] == self.TIPO_ADMIN),
        )

        return user


class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = [
            "nome_solicitante",
            "setor_local",
            "tipo_chamado",
            "descricao",
            "prioridade",
            "imagem",
        ]

        widgets = {
            "nome_solicitante": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "readonly": "readonly",
                }
            ),
            "setor_local": forms.Select(attrs={"class": "form-select"}),
            "tipo_chamado": forms.Select(attrs={"class": "form-select"}),
            "descricao": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Descreva o problema identificado, local exato e informações importantes para a equipe de manutenção.",
                }
            ),
            "prioridade": forms.Select(attrs={"class": "form-select"}),
            "imagem": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

        labels = {
            "nome_solicitante": "Nome do solicitante",
            "setor_local": "Setor / Local da solicitação",
            "tipo_chamado": "Tipo de chamado",
            "descricao": "Descrição do problema",
            "prioridade": "Prioridade",
            "imagem": "Anexo / imagem do problema",
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["setor_local"].empty_label = "Selecione o setor/local"
        self.fields["tipo_chamado"].empty_label = "Selecione o tipo de chamado"
        self.fields["prioridade"].empty_label = "Selecione a prioridade"

        if user and user.is_authenticated:
            nome = user.get_full_name() or user.username

            if hasattr(user, "perfil") and user.perfil.nome_completo:
                nome = user.perfil.nome_completo

            self.fields["nome_solicitante"].initial = nome


class ChamadoStatusForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ["status"]

        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class DashboardFiltroForm(forms.Form):
    setor_local = forms.ChoiceField(
        label="Setor / Local",
        required=False,
        choices=[("", "Todos")] + list(Chamado.SETOR_LOCAL),
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )

    status = forms.ChoiceField(
        label="Status",
        required=False,
        choices=[("", "Todos")] + list(Chamado.STATUS),
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )

    prioridade = forms.ChoiceField(
        label="Prioridade",
        required=False,
        choices=[("", "Todas")] + list(Chamado.PRIORIDADE),
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )

    data_inicio = forms.DateField(
        label="Data inicial",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
    )

    data_fim = forms.DateField(
        label="Data final",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
    )