from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Agendamento
from .forms import AgendamentoForm
from django.shortcuts import render, get_object_or_404
from .models import Cliente 
from .forms import ClienteForm
from datetime import timedelta
from django.http import JsonResponse
from datetime import datetime, timedelta, time
from .models import Agendamento, HorarioFuncionamento, Loja, Profissional, Servico
from django.utils.timezone import make_aware, is_naive, get_current_timezone
from django.utils import timezone



def horarios_disponiveis(request):
    from django.http import JsonResponse
    from django.utils.timezone import make_aware, get_current_timezone, localtime, is_naive
    from datetime import datetime, timedelta

    loja_id = request.GET.get("loja_id")
    profissional_id = request.GET.get("profissional_id")
    data_str = request.GET.get("data")
    servicos_ids = request.GET.get("servicos", "").split(",")

    if not loja_id or not profissional_id or not data_str or not servicos_ids:
        return JsonResponse({"horarios": [], "proximo": None})

    loja = Loja.objects.get(id=loja_id)
    profissional = Profissional.objects.get(id=profissional_id)
    servicos = Servico.objects.filter(id__in=servicos_ids)
    duracao_total = sum(s.duracao_minutos for s in servicos)

    data = datetime.strptime(data_str, "%Y-%m-%d").date()
    dia_semana = data.weekday()

    horario_loja = HorarioFuncionamento.objects.filter(loja=loja, dia_semana=dia_semana).first()
    hora_inicio = horario_loja.hora_abertura if horario_loja else loja.hora_abertura
    hora_fim = horario_loja.hora_fechamento if horario_loja else loja.hora_fechamento

    tz = get_current_timezone()
    inicio_loja = make_aware(datetime.combine(data, hora_inicio), tz)
    fim_loja = make_aware(datetime.combine(data, hora_fim), tz)

    # Agendamentos com timezone local
    agendamentos = []
    for ag in Agendamento.objects.filter(profissional=profissional, data_hora__date=data):
        ag_inicio = localtime(ag.data_hora)  # converte para timezone local
        ag_fim = ag_inicio + timedelta(minutes=sum(s.duracao_minutos for s in ag.servicos.all()))
        agendamentos.append((ag_inicio, ag_fim))

    horarios_livres = []
    proximo_horario = None
    h = inicio_loja

    while h + timedelta(minutes=duracao_total) <= fim_loja:
        inicio = localtime(h)  # garante timezone local
        fim = inicio + timedelta(minutes=duracao_total)
        conflito = False

        for ag_inicio, ag_fim in agendamentos:
            if inicio < ag_fim and fim > ag_inicio:  # sobreposição
                h = ag_fim  # pula para o fim do bloco ocupado
                conflito = True
                break

        if not conflito:
            horarios_livres.append(inicio.strftime("%H:%M"))
            if not proximo_horario:
                proximo_horario = inicio.strftime("%H:%M")
            h += timedelta(minutes=duracao_total)  # avança pelo tempo do agendamento
        # Se houver conflito, h já foi atualizado para o fim do agendamento em conflito

    return JsonResponse({"horarios": horarios_livres, "proximo": proximo_horario})


# Funções auxiliares

def gerar_intervalos(data, abertura, fechamento, duracao):
    tz = timezone.get_current_timezone()
    inicio = make_aware(datetime.combine(data, abertura), tz)
    fim = make_aware(datetime.combine(data, fechamento), tz)
    intervalo = timedelta(minutes=duracao)

    horarios = []
    atual = inicio
    while atual + intervalo <= fim:
        horarios.append((atual, atual + intervalo))
        atual += intervalo

    return horarios

def lista_clientes(request):
    clientes = Cliente.objects.all()  # pega todos os clientes
    return render(request, "ERPestetica/lista_clientes.html", {"clientes": clientes})
# Editar cliente

# Criar cliente
def criar_cliente(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente criado com sucesso!")
            return redirect("ERPestetica:lista_clientes")
    else:
        form = ClienteForm()
    return render(request, "ERPestetica/form_cliente.html", {"form": form, "acao": "Criar"})

def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente atualizado com sucesso!")
            return redirect("ERPestetica:lista_clientes")
    else:
        form = ClienteForm(instance=cliente)
    return render(request, "ERPestetica/form_cliente.html", {"form": form, "acao": "Editar"})

# Excluir cliente
def excluir_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        cliente.delete()
        messages.success(request, "Cliente excluído com sucesso!")
        return redirect("ERPestetica:lista_clientes")
    return render(request, "ERPestetica/confirmar_exclusao.html", {"cliente": cliente})


def criar_agendamento(request):
    if request.method == "POST":
        loja_id = request.POST.get("loja")
        data = request.POST.get("data")
        hora = request.POST.get("data_hora")

        # Monta o campo data_hora completo no formato ISO
        if data and hora:
            request.POST = request.POST.copy()
            request.POST["data_hora"] = f"{data}T{hora}"

        form = AgendamentoForm(request.POST)

        if form.is_valid():
            agendamento = form.save(commit=False)

            # Tornar data_hora timezone-aware
            data_hora = form.cleaned_data["data_hora"]
            if is_naive(data_hora):
                data_hora = make_aware(data_hora)
            agendamento.data_hora = data_hora

            # Calcula duração total dos serviços
            servicos_ids = request.POST.getlist("servicos")
            servicos = Servico.objects.filter(id__in=servicos_ids)
            duracao_total = sum(s.duracao_minutos for s in servicos)
            fim_novo = data_hora + timedelta(minutes=duracao_total)

            # Recupera agendamentos do mesmo dia para o mesmo profissional
            ag_prof = Agendamento.objects.filter(
                profissional=agendamento.profissional,
                data_hora__date=data_hora.date()
            )

            # Verifica conflitos com o profissional
            def tem_conflito_profissional(ag_list, inicio, fim):
                for ag in ag_list:
                    ag_inicio = ag.data_hora
                    ag_fim = ag_inicio + timedelta(minutes=sum(s.duracao_minutos for s in ag.servicos.all()))
                    if inicio < ag_fim and fim > ag_inicio:
                        return True
                return False

            if tem_conflito_profissional(ag_prof, data_hora, fim_novo):
                mensagem = "❌ Este profissional já está ocupado neste horário."
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"erro": mensagem})
                else:
                    messages.error(request, mensagem)
                    return redirect("/ERPestetica/")

            # Salva agendamento
            agendamento.save()
            form.save_m2m()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"sucesso": True})
            else:
                messages.success(request, "✅ Agendamento criado com sucesso!")
                return redirect("/ERPestetica/")

        else:
            print("⚠️ Erros no formulário:", form.errors.as_json())
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({
                    "erro": "⚠️ Dados inválidos. Verifique os campos.",
                    "detalhes": form.errors
                })

    # GET: exibe formulário
    form = AgendamentoForm()
    return render(request, "ERPestetica/criar_agendamento.html", {"form": form})


def lista_agendamentos(request):
    agendamentos = Agendamento.objects.all()
    profissionais = Profissional.objects.all()

    for ag in agendamentos:
        # Soma total de minutos dos serviços
        total_minutos = sum(serv.duracao_minutos for serv in ag.servicos.all())

        # Armazena duração total
        ag.duracao_total = timedelta(minutes=total_minutos)

        # Calcula o horário final (end_time)
        ag.end_time = ag.data_hora + timedelta(minutes=total_minutos)

    return render(request, "ERPestetica/lista_agendamentos.html", {
        "agendamentos": agendamentos,
        "profissionais": profissionais
    })

def detalhe_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)
    return render(request, "ERPestetica/detalhe_agendamento.html", {"agendamento": agendamento})

def alterar_status(request, pk):

    agendamento = get_object_or_404(Agendamento, pk=pk)
    if request.method == "POST":
        novo_status = request.POST.get("status")
        if novo_status in ['pendente', 'confirmado', 'cancelado']:
            agendamento.status = novo_status
            agendamento.save()
    return redirect('ERPestetica:detalhe_agendamento', pk=pk)



from django.http import JsonResponse
from .models import Profissional

def servicos_por_profissional(request):
    profissional_id = request.GET.get("profissional_id")

    try:
        profissional = Profissional.objects.get(id=profissional_id)
        servicos = profissional.servicos.all()  # ManyToMany

        data = {
            "servicos": [
                {"id": s.id, "nome": s.nome}
                for s in servicos
            ]
        }
        return JsonResponse(data)

    except Profissional.DoesNotExist:
        return JsonResponse({"servicos": []})
