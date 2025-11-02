from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.conf import settings
from django.utils.timezone import now, localtime
from .models import Servico, Demanda, TelegramLog
import requests
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


def home(request):
    return render(request, 'AppHome/home.html')

# =============================
#  🔹 PÁGINA INICIAL (LISTA DE SERVIÇOS)
# =============================
@login_required
def listar_servicos(request):
    servicos = Servico.objects.all().order_by("nome")
    return render(request, "AppHome/listar_servicos.html", {"servicos": servicos})


# =============================
#  🔹 LISTAR DEMANDAS
# =============================
@login_required
def listar_demandas(request):
    if request.user.is_superuser or request.user.groups.filter(name="Técnicos").exists():
        # Superuser vê todas as demandas
        demandas = Demanda.objects.all().order_by('-data_criacao')
    else:
        # Usuário comum vê apenas suas demandas
        demandas = Demanda.objects.filter(solicitante=request.user).order_by('-data_criacao')

    # ✅ Adiciona a verificação igual às outras views
    usuario_pode_alterar = request.user.is_superuser or request.user.groups.filter(name="Técnicos").exists()

    context = {
        'demandas': demandas,
        'usuario_pode_alterar': usuario_pode_alterar,  # 🔹 Passa para o template
    }
    context = {
        'demandas': demandas
    }
    return render(request, 'AppHome/listar_demandas.html', context)


# Função auxiliar para enviar mensagens ao Telegram
def enviar_telegram(texto):
    url = f'https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': settings.TELEGRAM_CHAT_ID,
        'text': texto
        # 'parse_mode': 'Markdown'  # Habilite se quiser formatação
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem para o Telegram: {e}")

# =============================
#  🔹 CRIAR NOVA DEMANDA
# =============================
@login_required
def nova_demanda(request):
    servicos = Servico.objects.all().order_by('nome')
    usuarios = User.objects.all().order_by('username') if request.user.is_superuser else None

    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        descricao_problema = request.POST.get('descricao_problema')
        servico_id = request.POST.get('servico')
        servico = get_object_or_404(Servico, id=servico_id)

        # Solicitante
        if request.user.is_superuser:
            solicitante_id = request.POST.get('solicitante')
            if not solicitante_id:
                messages.error(request, "Selecione um solicitante válido.")
                return redirect('AppHome:nova_demanda')
            solicitante = get_object_or_404(User, id=solicitante_id)
        else:
            solicitante = request.user
            if tipo == "Projeto":
                messages.error(request, "Você não tem permissão para criar um Projeto.")
                return redirect('AppHome:nova_demanda')

        # Criar demanda
        demanda = Demanda.objects.create(
            solicitante=solicitante,
            tipo=tipo,
            descricao_problema=descricao_problema,
            servico=servico,
            status='aberto',
            data_criacao=now()
        )

        # Campos TAP (somente admin e Projeto)
        if tipo == "Projeto" and request.user.is_superuser:
            demanda.objetivo = request.POST.get('objetivo')
            demanda.escopo = request.POST.get('escopo')
            demanda.justificativa = request.POST.get('justificativa')
            demanda.riscos = request.POST.get('riscos')
            demanda.prazos = request.POST.get('prazos')
            demanda.orcamento = request.POST.get('orcamento')
            demanda.responsaveis = request.POST.get('responsaveis')
            demanda.save()

        # 🔹 Formata data de criação
        data_criacao = localtime(demanda.data_criacao).strftime('%d/%m/%Y %H:%M')

        if demanda.tipo == 'Projeto':
            # Campos adicionais do projeto
            mensagem = (
                f"📢 *Novo Projeto Criado!*\n\n"
                f"🔖 *Tipo:* {demanda.tipo}\n"
                f"👤 *Solicitante:* {demanda.solicitante}\n"
                f"🛠️ *Serviço:* {demanda.servico}\n"
                f"📅 *Data de Abertura:* {data_criacao}\n"
                f"✅ *Executor:* {demanda.executor or 'A definir'}\n\n"
                f"📝 *Descrição do Problema:*\n{demanda.descricao_problema}\n\n"
                f"🎯 *Objetivo:* {demanda.objetivo}\n"
                f"📌 *Escopo:* {demanda.escopo}\n"
                f"💡 *Justificativa:* {demanda.justificativa}\n"
                f"⚠️ *Riscos:* {demanda.riscos}\n"
                f"⏱️ *Prazos:* {demanda.prazos}\n"
                f"💰 *Orçamento:* {demanda.orcamento}\n"
                f"👥 *Responsáveis:* {demanda.responsaveis}\n"
            )
        else:
            # Mensagem padrão para Chamado
            mensagem = (
                f"📢 *Nova Demanda Criada!*\n\n"
                f"🔖 *Tipo:* {demanda.tipo}\n"
                f"👤 *Solicitante:* {demanda.solicitante}\n"
                f"🛠️ *Serviço:* {demanda.servico}\n"
                f"📅 *Data de Abertura:* {data_criacao}\n"
                f"✅ *Executor:* {demanda.executor or 'A definir'}\n\n"
                f"📝 *Descrição do Problema:*\n{demanda.descricao_problema}\n"
            )

        enviar_telegram(mensagem)

        messages.success(request, "Demanda criada com sucesso!")
        return redirect('AppHome:listar_demandas')

    return render(request, "AppHome/nova_demanda.html", {"servicos": servicos, "usuarios": usuarios})



@login_required
def detalhar_demanda(request, id):
    demanda = get_object_or_404(Demanda, id=id)

    # ✅ Verifica se o usuário é superuser ou pertence ao grupo "Técnicos"
    usuario_pode_alterar = request.user.is_superuser or request.user.groups.filter(name="Técnicos").exists()

    
    # Guarda status antigo para comparar mudanças
    status_antigo = demanda.status

    # Se a demanda estiver aberta e o usuário puder alterar, passa para "Em Andamento"
    if demanda.status == 'aberto' and usuario_pode_alterar:
        demanda.status = 'Em Andamento'
        demanda.executor = request.user
        demanda.data_verificacao = now()
        demanda.save()

        # Envia mensagem de atualização para Telegram
        data_criacao = localtime(demanda.data_criacao).strftime('%d/%m/%Y %H:%M')
        data_verificacao = localtime(demanda.data_verificacao).strftime('%d/%m/%Y %H:%M')
        mensagem = (
            f"🔄 *Demanda Iniciada!*\n\n"
            f"🔖 *Tipo:* {demanda.tipo}\n"
            f"👤 *Solicitante:* {demanda.solicitante}\n"
            f"🛠️ *Serviço:* {demanda.servico}\n"
            f"📌 *Status Atual:* {demanda.status}\n"
            f"✅ *Executor:* {demanda.executor}\n"
            f"📅 *Data de Abertura:* {data_criacao}\n"
            f"🔎 *Data de Verificação:* {data_verificacao}\n\n"
            f"📝 *Descrição do Problema:*\n{demanda.descricao_problema}\n"
        )
        enviar_telegram(mensagem)

    # Processa POST apenas se o usuário puder alterar
    if request.method == 'POST' and usuario_pode_alterar:
        descricao_solucao = request.POST.get('descricao_solucao', '').strip()
        status_novo = request.POST.get('status')

        if descricao_solucao:
            # Atualiza solução
            if descricao_solucao:
                demanda.descricao_solucao = descricao_solucao

            # Atualiza status
            if status_novo:
                demanda.status = status_novo
                if status_novo.lower() == 'concluido':
                    demanda.data_solucao = now()
                # Detecta reabertura
                elif status_novo.lower() in ['aberto', 'em_andamento'] and status_antigo.lower() == 'concluido':
                    data_reabertura = localtime(now()).strftime('%d/%m/%Y %H:%M')
                    mensagem_reabertura = (
                        f"🔔 *Demanda Reaberta!*\n\n"
                        f"🔖 *Tipo:* {demanda.tipo}\n"
                        f"👤 *Solicitante:* {demanda.solicitante}\n"
                        f"🛠️ *Serviço:* {demanda.servico}\n"
                        f"📌 *Status Atual:* {demanda.status}\n"
                        f"✅ *Executor:* {request.user}\n"
                        f"📅 *Data de Reabertura:* {data_reabertura}\n\n"
                        f"📝 *Descrição do Problema:*\n{demanda.descricao_problema}\n"
                    )
                    enviar_telegram(mensagem_reabertura)

            demanda.save()

            # Envia mensagem de conclusão se necessário
            if demanda.status.lower() == 'concluido':
                data_solucao = localtime(demanda.data_solucao).strftime('%d/%m/%Y %H:%M') if demanda.data_solucao else None
                mensagem = (
                    f"✅ *Demanda Finalizada!*\n\n"
                    f"🔖 *Tipo:* {demanda.tipo}\n"
                    f"🛠️ *Serviço:* {demanda.servico}\n"
                    f"👤 *Executor:* {demanda.executor}\n"
                    f"📅 *Data de Solução:* {data_solucao}\n\n"
                    f"📝 *Descrição do Problema:*\n{demanda.descricao_problema}\n"
                    f"📝 *Solução:* {demanda.descricao_solucao}\n"
                )
                enviar_telegram(mensagem)

            messages.success(request, "Demanda atualizada com sucesso.")
            return redirect('AppHome:listar_demandas')
        else:
            messages.warning(request, "Preencha a descrição da solução ou altere o status antes de salvar.")

    return render(request, 'AppHome/detalhar_demanda.html', {
        'demanda': demanda,
        'usuario_pode_alterar': usuario_pode_alterar
    })



# =============================
#  🔹 EDITAR / ATUALIZAR UMA DEMANDA
# =============================
@login_required
def editar_demanda(request, id):
    demanda = get_object_or_404(Demanda, id=id)

    # ✅ Verifica se o usuário é superuser ou pertence ao grupo "Técnicos"
    usuario_pode_alterar = request.user.is_superuser or request.user.groups.filter(name="Técnicos").exists()

    if not usuario_pode_alterar:
        messages.warning(request, "Você não tem permissão para editar esta demanda.")
        return redirect('AppHome:detalhar_demanda', id=demanda.id)

    # Guarda status antigo para detectar reabertura ou conclusão
    status_antigo = demanda.status

    if request.method == "POST":
        descricao_solucao = request.POST.get("descricao_solucao", "").strip()
        status_novo = request.POST.get("status", "").lower()  # Padronizando para lowercase

        if not descricao_solucao and not status_novo:
            messages.warning(request, "Preencha a descrição da solução ou altere o status antes de salvar.")
            return redirect('AppHome:editar_demanda', id=demanda.id)

        # Atualiza descrição da solução
        if descricao_solucao:
            demanda.descricao_solucao = descricao_solucao

        # Atualiza status
        if status_novo:
            demanda.status = status_novo

            # Marca conclusão
            if status_novo == 'concluido' and not demanda.data_solucao:
                demanda.data_solucao = now()
                data_solucao = localtime(demanda.data_solucao).strftime('%d/%m/%Y %H:%M')
                mensagem = (
                    f"✅ *Demanda Finalizada!*\n\n"
                    f"🔖 *Tipo:* {demanda.tipo}\n"
                    f"🛠️ *Serviço:* {demanda.servico}\n"
                    f"👤 *Executor:* {demanda.executor}\n"
                    f"📅 *Data de Solução:* {data_solucao}\n\n"
                    f"📝 *Descrição do Problema:*\n{demanda.descricao_problema}\n"
                    f"📝 *Solução:* {demanda.descricao_solucao}\n"
                )
                enviar_telegram(mensagem)

            # Detecta reabertura
            elif status_novo in ['aberto', 'em_andamento'] and status_antigo == 'concluido':
                data_reabertura = localtime(now()).strftime('%d/%m/%Y %H:%M')
                mensagem_reabertura = (
                    f"🔔 *Demanda Reaberta!*\n\n"
                    f"🔖 *Tipo:* {demanda.tipo}\n"
                    f"👤 *Solicitante:* {demanda.solicitante}\n"
                    f"🛠️ *Serviço:* {demanda.servico}\n"
                    f"📌 *Status Atual:* {demanda.status}\n"
                    f"✅ *Executor:* {request.user}\n"
                    f"📅 *Data de Reabertura:* {data_reabertura}\n\n"
                    f"📝 *Descrição do Problema:*\n{demanda.descricao_problema}\n"
                )
                enviar_telegram(mensagem_reabertura)

        # Salva alterações
        demanda.save()
        messages.success(request, "Demanda atualizada com sucesso!")
        return redirect('AppHome:listar_demandas')

    return render(request, "AppHome/editar_demanda.html", {
        "demanda": demanda,
        "usuario_pode_alterar": usuario_pode_alterar
    })


# =============================
#  🔹 EXCLUIR DEMANDA
# =============================
@login_required
def excluir_demanda(request, id):
    demanda = get_object_or_404(Demanda, id=id)
    if request.method == "POST":
        demanda.delete()
        messages.success(request, "Demanda excluída com sucesso!")
        return redirect("AppHome:listar_demandas")

    return render(request, "AppHome/excluir_demanda.html", {"demanda": demanda})


# =============================
#  🔹 REGISTRAR LOG NO TELEGRAM (opcional)
# =============================
def registrar_log_telegram(destinatario, mensagem, sucesso=True, erro=None):
    TelegramLog.objects.create(
        destinatario=destinatario,
        mensagem=mensagem,
        sucesso=sucesso,
        erro=erro,
    )

# =============================
#  🔹 Dashboard
# =============================
@login_required
def dashboard(request):
    # Permitir apenas superusuários e membros do grupo "Técnicos"
    is_executor = request.user.groups.filter(name="Técnicos").exists()

    if not (request.user.is_superuser or is_executor):
        messages.warning(request, "Você não tem permissão para acessar o dashboard.")
        return redirect('AppHome:listar_demandas')

    total_demandas = Demanda.objects.count()
    abertas = Demanda.objects.filter(status='aberto').count()
    em_andamento = Demanda.objects.filter(status='Em Andamento').count()
    concluidas = Demanda.objects.filter(status='Concluído').count()
    demandas_recentes = Demanda.objects.order_by('-data_criacao')[:5]
    servicos = Servico.objects.all()

    context = {
        'total_demandas': total_demandas,
        'abertas': abertas,
        'em_andamento': em_andamento,
        'concluidas': concluidas,
        'demandas_recentes': demandas_recentes,
        'servicos': servicos,
        'is_executor': is_executor,  # 👈 Adiciona variável para o template
    }
    return render(request, 'AppHome/dashboard.html', context)


@login_required
def dashboard_data(request):
    if not (request.user.is_superuser or request.user.groups.filter(name="Técnicos").exists()):
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    total_demandas = Demanda.objects.count()
    abertas = Demanda.objects.filter(status='aberto').count()
    em_andamento = Demanda.objects.filter(status='Em Andamento').count()
    concluidas = Demanda.objects.filter(status='Concluído').count()
    
    demandas_recentes = list(
        Demanda.objects.order_by('-data_criacao')[:5].values(
            'id', 'servico__nome', 'tipo', 'solicitante__username', 'status', 'data_criacao'
        )
    )
    
    servicos = list(
        Servico.objects.all().values('nome', 'categoria', 'modelo_cobranca', 'status')
    )

    return JsonResponse({
        'total_demandas': total_demandas,
        'abertas': abertas,
        'em_andamento': em_andamento,
        'concluidas': concluidas,
        'demandas_recentes': demandas_recentes,
        'servicos': servicos,
    })

def logout_get(request):
    logout(request)
    return redirect('/')