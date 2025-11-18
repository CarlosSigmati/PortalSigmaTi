from django import forms
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import Agendamento, Servico, Cliente, Loja, HorarioFuncionamento
from django.db.models import Max
from datetime import timedelta, datetime
from django.utils.timezone import make_aware, is_naive, get_current_timezone
from django.utils.timezone import localtime


class AgendamentoForm(forms.ModelForm):
    servicos = forms.ModelMultipleChoiceField(
        queryset=Servico.objects.filter(ativo=True),
        widget=forms.CheckboxSelectMultiple,
        label="Serviços disponíveis"
    )

    class Meta:
        model = Agendamento
        fields = ["cliente", "loja", "profissional", "servicos", "data_hora", "observacoes", "status"]
        widgets = {
            "data_hora": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "observacoes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "cliente": forms.Select(attrs={"class": "form-select"}),
            "loja": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        profissional = kwargs.pop('profissional', None)
        super().__init__(*args, **kwargs)
        # Filtra serviços apenas do profissional, se fornecido
        if profissional:
            self.fields['servicos'].queryset = Servico.objects.filter(ativo=True, profissionais=profissional)

    def clean(self):
        cleaned_data = super().clean()
        loja = cleaned_data.get("loja")
        profissional = cleaned_data.get("profissional")
        data_hora = cleaned_data.get("data_hora")
        servicos = cleaned_data.get("servicos")

        if not loja or not profissional or not data_hora or not servicos:
            return cleaned_data

        tz = get_current_timezone()
        if is_naive(data_hora):
            data_hora = make_aware(data_hora, tz)
        cleaned_data['data_hora'] = data_hora

        # Horário da loja
        dia_semana = data_hora.weekday()
        horario = HorarioFuncionamento.objects.filter(loja=loja, dia_semana=dia_semana).first()
        hora_abertura = horario.hora_abertura if horario else loja.hora_abertura
        hora_fechamento = horario.hora_fechamento if horario else loja.hora_fechamento

        # Duração total do agendamento
        duracao_total = sum(s.duracao_minutos for s in servicos)
        data_fim = data_hora + timedelta(minutes=duracao_total)
        print(f"Tentando criar: {data_hora} - {data_fim}")

        # Valida expediente
        if not (hora_abertura <= data_hora.time() and data_fim.time() <= hora_fechamento):
            raise ValidationError(
                f"A loja {loja.nome} funciona das {hora_abertura.strftime('%H:%M')} às {hora_fechamento.strftime('%H:%M')}."
            )

        # Conflito com agendamentos existentes
        # Conflito com agendamentos existentes
        agendamentos_prof = Agendamento.objects.filter(
            profissional=profissional,
            data_hora__date=data_hora.date()
        )

        intervalo_minutos = 0  # intervalo mínimo
        for ag in agendamentos_prof:
            ag_inicio = localtime(ag.data_hora)  # converte para timezone local
            ag_fim = ag_inicio + timedelta(minutes=sum(s.duracao_minutos for s in ag.servicos.all()))
            print(f"Ag existente: {ag_inicio} - {ag_fim}")

            # Verifica sobreposição real
            if data_hora < ag_fim + timedelta(minutes=intervalo_minutos) and data_fim + timedelta(minutes=intervalo_minutos) > ag_inicio:
                raise ValidationError(
                    f"❌ Conflito com agendamento existente do profissional das {ag_inicio.strftime('%H:%M')} às {ag_fim.strftime('%H:%M')}."
                )

        return cleaned_data

    @staticmethod
    def proximo_horario_disponivel(loja, profissional, data, duracao_total):
        """Retorna o próximo horário disponível para a data e profissional"""
        dia_semana = data.weekday()
        horario = HorarioFuncionamento.objects.filter(loja=loja, dia_semana=dia_semana).first()
        hora_abertura = horario.hora_abertura if horario else loja.hora_abertura
        hora_fechamento = horario.hora_fechamento if horario else loja.hora_fechamento

        tz = get_current_timezone()
        inicio_loja = make_aware(datetime.combine(data, hora_abertura), tz)
        fim_loja = make_aware(datetime.combine(data, hora_fechamento), tz)

        agendamentos = [
            (localtime(ag.data_hora), localtime(ag.data_hora) + timedelta(minutes=sum(s.duracao_minutos for s in ag.servicos.all())))
            for ag in Agendamento.objects.filter(profissional=profissional, data_hora__date=data)
        ]


        h = inicio_loja
        intervalo = timedelta(minutes=1)
        while h + timedelta(minutes=duracao_total) <= fim_loja:
            inicio = h
            fim = h + timedelta(minutes=duracao_total)
            conflito = False
            for ag_inicio, ag_fim in agendamentos:
                if inicio < ag_fim and fim > ag_inicio:
                    h = ag_fim
                    conflito = True
                    break
            if not conflito:
                return h.time().strftime("%H:%M")
            h += intervalo
        return None


class ClienteForm(forms.ModelForm):
    loja = forms.ModelChoiceField(
        queryset=Loja.objects.all(),
        required=False,
        empty_label="Selecione uma loja",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Cliente
        fields = ['nome', 'telefone', 'email', 'loja']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do cliente'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de telefone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }
