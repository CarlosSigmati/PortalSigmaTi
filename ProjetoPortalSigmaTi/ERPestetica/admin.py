from django.contrib import admin
from .models import Loja, Cliente, Servico, Agendamento, HorarioFuncionamento, Profissional

@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone", "email", "ativo")
    search_fields = ("nome", "telefone", "email")
    list_filter = ("ativo",)


@admin.register(HorarioFuncionamento)
class HorarioFuncionamentoAdmin(admin.ModelAdmin):
    list_display = ("loja", "dia_semana", "hora_abertura", "hora_fechamento")
    list_filter = ("loja", "dia_semana")
    ordering = ("loja", "dia_semana")

@admin.register(Loja)
class LojaAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone", "email")
    search_fields = ("nome", "endereco")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone", "email", "data_cadastro")
    search_fields = ("nome", "cpf_cnpj", "telefone")


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "preco", "duracao_minutos", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "loja", "profissional", "data_hora", "status")
    list_filter = ("status", "loja", "profissional")
    search_fields = ("cliente__nome", "loja__nome", "profissional__nome")
    filter_horizontal = ("servicos",)

