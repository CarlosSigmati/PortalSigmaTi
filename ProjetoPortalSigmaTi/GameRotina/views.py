from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import PlayerProgress, Rotina, Badge
from .forms import RotinaForm
from django.utils import timezone
from datetime import datetime, time
import cv2
import numpy as np
import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import PlayerProgress, Rotina
from .forms import RotinaForm
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
            rotina.enviado = True
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



import cv2
import numpy as np
import base64
import json
import threading
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# === Variáveis globais ===
imagem_referencia = None
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# === Funções utilitárias ===
def decodificar_imagem(imagem_base64: str) -> np.ndarray:
    """Decodifica uma imagem em Base64 (com ou sem prefixo data:image/...)"""
    try:
        if "," in imagem_base64:
            imagem_base64 = imagem_base64.split(",")[1]
        imagem_bytes = base64.b64decode(imagem_base64)
        np_arr = np.frombuffer(imagem_bytes, np.uint8)
        return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"⚠️ Erro ao decodificar imagem: {e}")
        return None


def codificar_imagem_para_base64(imagem_cv2: np.ndarray, formato: str = ".jpg") -> str:
    """Codifica imagem OpenCV em Base64 (retorna data URL pronto para exibir)"""
    try:
        _, buffer = cv2.imencode(formato, imagem_cv2)
        img_base64 = base64.b64encode(buffer).decode("utf-8")
        return f"data:image/jpeg;base64,{img_base64}"
    except Exception as e:
        print(f"⚠️ Erro ao codificar imagem: {e}")
        return ""


# === View: salvar referência ===
@csrf_exempt
def salvar_referencia(request):
    """Salva a imagem de referência para futuras comparações"""
    global imagem_referencia

    if request.method != "POST":
        return JsonResponse({"erro": "Método não permitido."}, status=405)

    try:
        dados = json.loads(request.body)
        imagem_referencia = decodificar_imagem(dados.get("imagem", ""))

        if imagem_referencia is None:
            return JsonResponse({"salvo": False, "erro": "Imagem inválida."}, status=400)

        # Pré-processamento: suavização leve
        imagem_referencia = cv2.GaussianBlur(imagem_referencia, (3, 3), 0)
        cv2.imwrite("referencia_capturada.jpg", imagem_referencia)

        print("✅ Imagem de referência salva com sucesso.")
        return JsonResponse({"salvo": True})
    except Exception as e:
        print(f"❌ Erro ao salvar referência: {e}")
        return JsonResponse({"salvo": False, "erro": str(e)}, status=500)


# === Função: processamento pesado ===
def processar_comparacao(imagem_ref: np.ndarray, imagem_atual: np.ndarray, resultado_dict: dict):
    """Processa a comparação entre imagem atual e referência"""
    try:
        # Pré-processamento
        imagem_proc = cv2.GaussianBlur(imagem_atual, (3, 3), 0)
        gray_ref = cv2.cvtColor(imagem_ref, cv2.COLOR_BGR2GRAY)
        gray_atual = cv2.cvtColor(imagem_proc, cv2.COLOR_BGR2GRAY)

        # --- Template Matching ---
        try:
            result = cv2.matchTemplate(gray_atual, gray_ref, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
        except Exception:
            max_val = 0.0

        # --- ORB Matching ---
        orb = cv2.ORB_create(nfeatures=500)
        kp1, des1 = orb.detectAndCompute(gray_ref, None)
        kp2, des2 = orb.detectAndCompute(gray_atual, None)
        similaridade_orb = 0
        if des1 is not None and des2 is not None:
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(des1, des2)
            similaridade_orb = len(matches)

        # --- Detecção de rostos ---
        faces = face_cascade.detectMultiScale(gray_atual, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        for (x, y, w, h) in faces:
            cv2.rectangle(imagem_proc, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # --- Resultado combinado ---
        detectado = (max_val > 0.55) or (similaridade_orb > 25) or (len(faces) > 0)

        resultado_dict.update({
            "detectado": bool(detectado),
            "template_score": round(float(max_val), 3),
            "orb_matches": int(similaridade_orb),
            "faces_count": int(len(faces)),
            "imagem_resultante_base64": codificar_imagem_para_base64(imagem_proc)
        })

    except Exception as e:
        print(f"❌ Erro no processamento da comparação: {e}")
        resultado_dict.update({
            "detectado": False,
            "template_score": 0.0,
            "orb_matches": 0,
            "faces_count": 0,
            "erro": str(e)
        })


# === View: verificar item ===
@csrf_exempt
def verificar_item(request):
    """Compara o frame atual com a imagem de referência"""
    global imagem_referencia

    if request.method != "POST":
        return JsonResponse({"erro": "Método não permitido."}, status=405)

    if imagem_referencia is None:
        return JsonResponse({"detectado": False, "mensagem": "Nenhuma imagem de referência salva."}, status=400)

    try:
        dados = json.loads(request.body)
        imagem_atual = decodificar_imagem(dados.get("imagem", ""))
        if imagem_atual is None:
            return JsonResponse({"erro": "Imagem atual inválida."}, status=400)

        resultado = {}
        worker = threading.Thread(target=processar_comparacao, args=(imagem_referencia, imagem_atual, resultado))
        worker.start()
        worker.join()

        print(
            f"🎯 Template={resultado.get('template_score', 0):.2f} | "
            f"ORB={resultado.get('orb_matches', 0)} | "
            f"Faces={resultado.get('faces_count', 0)} | "
            f"Detectado={resultado.get('detectado', False)}"
        )

        return JsonResponse(resultado)
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return JsonResponse({"detectado": False, "erro": str(e)}, status=500)
