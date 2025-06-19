from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportMixin
from .models import LinkUtil, Cliente, Contato, Servico, Demanda
from django.shortcuts import redirect
from django.contrib import messages
import requests
from django.conf import settings
from django.utils.timezone import now, localtime


# Criando um recurso de exportação para o modelo Servico
class ServicoResource(resources.ModelResource):
    class Meta:
        model = Servico
        fields = ('id', 'nome', 'descricao', 'valor', 'categoria', 'modelo_cobranca', 'requisitos', 'ferramentas', 
                  'tempo_medio_execucao', 'nivel_complexidade', 'status', 'documentacao')
    
    
@admin.register(LinkUtil)
class LinkUtilAdmin(admin.ModelAdmin):
    list_display = ('nome', 'url')
    search_fields = ('nome',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf_cnpj', 'telefone_cliente', 'email', 'data_contrato', 'tipo', 'listar_responsaveis')
    list_filter = ('tipo', 'data_contrato', 'usuarios_responsaveis')
    search_fields = ('nome', 'cpf_cnpj', 'email')
    filter_horizontal = ('usuarios_responsaveis',)

    def telefone_cliente(self, obj):
        return obj.contato.telefone  # Puxa o telefone do Contato relacionado
    telefone_cliente.short_description = 'Telefone'

    def listar_responsaveis(self, obj):
        return ", ".join([user.username for user in obj.usuarios_responsaveis.all()])
    listar_responsaveis.short_description = 'Responsáveis'

@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf_cnpj_cliente', 'email', 'contato_numero', 'tipo')
    search_fields = ('nome', 'tipo', 'email', 'empresa')
    list_filter = ('empresa', 'tipo', 'email')

    def cpf_cnpj_cliente(self, obj):
        # Acessa o cpf_cnpj do Cliente relacionado através da relação reversa
        cliente = obj.cliente_set.first()  # Assumindo que cada Contato pode ter apenas um Cliente
        return cliente.cpf_cnpj if cliente else None  # Caso exista um cliente relacionado
    cpf_cnpj_cliente.short_description = 'CPF/CNPJ'  # Personaliza o nome da coluna

    def contato_numero(self, obj):
        return obj.telefone  # Ou outro campo de contato relacionado
    contato_numero.short_description = 'Contato'

    def data_contrato(self, obj):
        cliente = obj.cliente_set.first()  # Assumindo que cada Contato pode ter apenas um Cliente
        return cliente.data_contrato.strftime('%d/%m/%Y') if cliente else None
    data_contrato.short_description = 'Data do Contrato'

@admin.register(Servico)
class ServicoAdmin(ImportExportMixin,admin.ModelAdmin):
    # Campos exibidos na lista do admin
    list_display = ('nome', 'descricao', 'categoria', 'modelo_cobranca', 'valor', 'tempo_medio_execucao', 'nivel_complexidade',)
    # Filtros para facilitar a pesquisa no admin
    list_filter = ('categoria', 'modelo_cobranca', 'status', 'nivel_complexidade')
    # Campos que podem ser pesquisados diretamente no admin
    search_fields = ('nome', 'descricao', 'categoria', 'modelo_cobranca')
    # Campos para adicionar ou editar no form de admin
    fields = ('nome', 'descricao', 'valor', 'categoria', 'modelo_cobranca', 'requisitos', 'ferramentas', 'tempo_medio_execucao', 'nivel_complexidade', 'status', 'documentacao')
    # Atributos adicionais de estilo no admin
    ordering = ('nome',)  # Ordena os itens pelo nome de forma padrão

    resource_class = ServicoResource  # Associando o recurso de exportação ao admin

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Quando o objeto já foi salvo, torne esses campos apenas leitura
            return ['nome', 'descricao', 'modelo_cobranca','requisitos',]
        return []

def enviar_telegram(texto):
    url = f'https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': settings.TELEGRAM_CHAT_ID,
        'text': texto
        #'parse_mode': 'Markdown'  # Permite formatação Markdown
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem para o Telegram: {e}")

@admin.register(Demanda)
class DemandaAdmin(admin.ModelAdmin):
    list_display = ('solicitante','status','tipo', 'descricao_problema', 'servico', 'data_criacao', 'executor')
    list_filter = ('tipo', 'status', 'solicitante', 'servico', 'executor')
    search_fields = ('descricao_problema','descricao_solucao', 'solicitante__nome', 'servico__nome', 'executor')
    ordering = ('data_criacao',)

    def save_model(self, request, obj, form, change):
        novo = not change  # Verifica se é uma criação nova

        if novo and not request.user.is_superuser:  # Se for novo e não for superuser
            obj.solicitante = request.user

        super().save_model(request, obj, form, change)

        # Se o campo de solução for preenchido e a data não, marca como concluído
        if obj.descricao_solucao and not obj.data_solucao:
            obj.data_solucao = now()
            obj.status = 'Concluído'
            obj.save()
        elif obj.descricao_solucao and obj.data_solucao:
            obj.data_solucao = now()
            obj.status = 'Concluído'
            obj.save()

        # Convertendo datas para horário local
        data_criacao = localtime(obj.data_criacao).strftime('%d/%m/%Y %H:%M')
        data_verificacao = localtime(obj.data_verificacao).strftime('%d/%m/%Y %H:%M') if obj.data_verificacao else None
        data_solucao = localtime(obj.data_solucao).strftime('%d/%m/%Y %H:%M') if obj.data_solucao else None
        ultima_atualizacao = localtime(now()).strftime('%d/%m/%Y %H:%M')

        # ✅ ENVIO PARA TELEGRAM
        if novo:
            mensagem = (
                f"📢 *Nova Demanda Criada!*\n\n"
                f"🔖 *Tipo:* {obj.tipo}\n"
                f"👤 *Solicitante:* {obj.solicitante}\n"
                f"🛠️ *Serviço:* {obj.servico}\n"
                f"📅 *Data de Abertura:* {data_criacao}\n"
                f"✅ *Executor:* {obj.executor or 'A definir'}\n"
                f"\n📝 *Descrição do Problema:*\n{obj.descricao_problema}\n"
            )
            enviar_telegram(mensagem)

        elif change:
            mensagem = (
                f"🔄 *Demanda Atualizada!*\n\n"
                f"🔖 *Tipo:* {obj.tipo}\n"
                f"👤 *Solicitante:* {obj.solicitante}\n"
                f"🛠️ *Serviço:* {obj.servico}\n"
                f"📌 *Status Atual:* {obj.status}\n"
                f"✅ *Executor:* {obj.executor or 'A definir'}\n"
                f"📅 *Data de Abertura:* {data_criacao}\n"
            )

            if data_verificacao:
                mensagem += f"🔎 *Data de Verificação:* {data_verificacao}\n"

            if data_solucao:
                mensagem += f"✅ *Data de Solução:* {data_solucao}\n"

            mensagem += (
                f"\n📝 *Descrição do Problema:*\n{obj.descricao_problema}\n"
                f"\n✅ *Descrição da Solução:*\n{obj.descricao_solucao or 'Ainda não informada.'}\n"
                f"\n🕒 *Última Atualização:* {ultima_atualizacao}"
            )
            enviar_telegram(mensagem)

    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return ['tipo', 'descricao_problema', 'solicitante', 'servico', 'data_criacao','data_verificacao', 'status','executor','data_solucao']
        
        elif not request.user.is_superuser:
            return ['solicitante', 'status','descricao_solucao', 'data_solucao','data_verificacao', 'executor']
        elif obj and request.user.is_superuser and obj.data_solucao:
            return ['tipo', 'descricao_problema', 'solicitante', 'servico', 'descricao_solucao','data_criacao','data_verificacao', 'status','data_solucao','executor']
        
        elif obj and request.user.is_superuser:
            return ['tipo', 'descricao_problema', 'solicitante', 'servico', 'data_criacao','data_verificacao', 'status','data_solucao','executor']
        
        elif not obj and request.user.is_superuser:
            return [ 'status','descricao_solucao', 'data_solucao','data_verificacao', 'executor']
        return []
    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and obj.status == 'Aberto':
            from django.utils.timezone import now
            obj.data_verificacao = now()
            obj.status = 'Em Andamento'
            obj.executor = request.user
            obj.save()
            return redirect(request.path)  # Refresh da página após salvar a mudança
        return super().change_view(request, object_id, form_url, extra_context)
   