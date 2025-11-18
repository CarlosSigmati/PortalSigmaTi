from django import forms
from .models import Anamnese

class AnamneseForm(forms.ModelForm):
    class Meta:
        model = Anamnese
        fields = "__all__"

        textarea_fields = [
            "motivo_consulta",
            "expectativas",
            "tratamento_medico_qual",
            "medicamentos_detalhes",
            "suplementos_quais",
            "alergias_quais",
            "condicoes_saude",
            "hospitalizado_detalhes",
            "drogas_quais_frequencia",
        ]

        widgets = {
            field: forms.Textarea(attrs={"rows": 3})
            for field in textarea_fields
        }
