from django import forms

from .models import Chamado


class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ['setor', 'equipamento', 'descricao', 'prioridade', 'imagem']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 5}),
        }


class ChamadoStatusForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ['status']

