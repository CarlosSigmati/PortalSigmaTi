from django import forms  # ⚠️ Certifique-se que está aqui
from .models import Rotina

class RotinaForm(forms.ModelForm):
    class Meta:
        model = Rotina
        fields = [
            'leitura',
            'arte_marcial',
            'limpar_casa',
            'musculacao',
            'alimentacao_saudavel',
            'copos_agua',  # adiciona aqui
        ]
        widgets = {
            'leitura': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'arte_marcial': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'limpar_casa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'musculacao': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'alimentacao_saudavel': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'copos_agua': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 16,
                'step': 1
            }),
        }
