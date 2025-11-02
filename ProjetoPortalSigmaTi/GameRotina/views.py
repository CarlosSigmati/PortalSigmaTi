from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import PlayerProgress, Rotina, Badge
from .forms import RotinaForm
from django.utils import timezone
from datetime import datetime, time
@login_required
def dashboard_jogo(request):
    player, _ = PlayerProgress.objects.get_or_create(user=request.user)
    rotinas = Rotina.objects.filter(user=request.user).order_by('-data_hora')
    pontos_ganhos = 0

    # Calcular XP para o próximo nível
    xp_proximo_nivel = (player.nivel + 1) * 100
    porcentagem_xp = (player.pontos_totais / xp_proximo_nivel) * 100

    if request.method == "POST":
        form = RotinaForm(request.POST)
        if form.is_valid():
            rotina = form.save(commit=False)
            rotina.user = request.user
            rotina.calcular_pontos()
            rotina.save()

            player.pontos_totais += rotina.pontos
            player.atualizar_streak()
            player.calcular_nivel()
            player.verificar_conquistas()
            pontos_ganhos = rotina.pontos
            player.save()

            return redirect('GameRotina:dashboard_jogo')
    else:
        form = RotinaForm()

    ranking = PlayerProgress.objects.all().order_by('-pontos_totais')[:10]

    return render(request, 'GameRotina/dashboard_jogo.html', {
        'player': player,
        'rotinas': rotinas,
        'form': form,
        'pontos_ganhos': pontos_ganhos,
        'ranking': ranking,
        'xp_proximo_nivel': xp_proximo_nivel,
        'porcentagem_xp': porcentagem_xp,
    })

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import PlayerProgress, Rotina
from .forms import RotinaForm
from datetime import datetime, time

@login_required
def jogo(request):
    user = request.user
    hoje = timezone.now().date()

    # Definir intervalo do dia (SQLite não aceita __date)
    inicio_hoje = timezone.make_aware(datetime.combine(hoje, time.min))
    fim_hoje = timezone.make_aware(datetime.combine(hoje, time.max))

    # Pega ou cria PlayerProgress
    player, _ = PlayerProgress.objects.get_or_create(user=user)

    # Pega rotina de hoje, se existir
    rotina_hoje = Rotina.objects.filter(user=user, data_hora__range=(inicio_hoje, fim_hoje)).first()

    pontos_ganhos = None

    if request.method == 'POST':
        form = RotinaForm(request.POST, instance=rotina_hoje)
        if form.is_valid():
            rotina = form.save(commit=False)
            rotina.user = user
            rotina.data_hora = timezone.now()
            rotina.calcular_pontos()
            rotina.save()

            # Atualiza pontos, streak e nível do jogador
            player.pontos_totais += rotina.pontos
            player.atualizar_streak()
            player.calcular_nivel()
            player.verificar_conquistas()
            player.save()

            pontos_ganhos = rotina.pontos
            rotina_hoje = rotina

            return redirect('GameRotina:jogo')  # evita reenvio de form
    else:
        form = RotinaForm(instance=rotina_hoje)

    # Histórico das últimas 10 rotinas
    rotinas = Rotina.objects.filter(user=user).order_by('-data_hora')[:10]

    # XP para o próximo nível (usar propriedade sem parênteses)
    xp_proximo_nivel = player.xp_proximo_nivel
    porcentagem_xp = (player.pontos_totais / ((player.nivel) * 100 + xp_proximo_nivel)) * 100

    context = {
        'form': form,
        'rotina_hoje': rotina_hoje,
        'rotinas': rotinas,
        'player': player,
        'xp_proximo_nivel': xp_proximo_nivel,
        'porcentagem_xp': porcentagem_xp,
        'pontos_ganhos': pontos_ganhos,
    }

    return render(request, 'GameRotina/jogo.html', context)
