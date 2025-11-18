from django.shortcuts import render
from django.http import JsonResponse
from .forms import AnamneseForm
from .models import Anamnese
import base64
from django.core.files.base import ContentFile
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Anamnese

def anamnese_view(request):
    if request.method == "POST":
        form = AnamneseForm(request.POST)
        assinatura_base64 = request.POST.get("assinatura")

        if form.is_valid() and assinatura_base64:
            anamnese = form.save(commit=False)

            # Converter assinatura base64
            formato, imgstr = assinatura_base64.split(";base64,")
            ext = formato.split("/")[-1]

            # Salvar assinatura do paciente
            anamnese.assinatura_paciente.save(
                f"assinatura_paciente_{anamnese.nome}.{ext}",
                ContentFile(base64.b64decode(imgstr)),
                save=False
            )

            anamnese.save()

            return JsonResponse({"status": "ok", "mensagem": "Anamnese salva com sucesso!"})
        else:
            return JsonResponse({"status": "erro", "mensagem": "Dados inválidos!"})

    form = AnamneseForm()
    return render(request, "Exames/anamnese.html", {"form": form})

def exames_crud(request):
    search = request.GET.get("search", "")

    exames = Anamnese.objects.all().order_by('-id')  # Ordena por id decrescente

    if search:
        exames = exames.filter(nome__icontains=search)  # Filtra pelo nome

    return render(request, 'Exames/exames_crud.html', {
        "exames": exames,
        "search": search
    })

def excluir_exame(request, exame_id):
    exame = get_object_or_404(Anamnese, id=exame_id)
    exame.delete()
    return redirect('Exames:exames_crud')

def imprimir_exame(request, exame_id):
    exame = get_object_or_404(Anamnese, id=exame_id)
    return render(request, 'Exames/imprimir_exame.html', {'exame': exame})

