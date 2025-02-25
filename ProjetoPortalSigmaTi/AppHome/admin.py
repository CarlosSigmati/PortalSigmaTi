from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportMixin
from .models import LinkUtil, Cliente, Contato, Servico, Demanda
from django.shortcuts import redirect
from django.contrib import messages

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
    list_display = ('nome', 'cpf_cnpj', 'telefone_cliente', 'email', 'data_contrato', 'tipo')
    list_filter = ('tipo', 'data_contrato')
    search_fields = ('nome', 'cpf_cnpj', 'email')

    def telefone_cliente(self, obj):
        return obj.contato.telefone  # Acessa o telefone do Contato relacionado
    telefone_cliente.short_description = 'Telefone'

@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf_cnpj_cliente', 'email', 'contato_numero', 'data_contrato', 'tipo')
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

@admin.register(Demanda)
class DemandaAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'descricao_problema', 'solicitante', 'servico', 'data_criacao', 'status', 'executor')
    list_filter = ('tipo', 'status', 'solicitante', 'servico', 'executor')
    search_fields = ('descricao_problema','descricao_solucao', 'solicitante__nome', 'servico__nome', 'executor')
    ordering = ('data_criacao',)

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:  # Apenas para não-superusuários
            obj.solicitante = request.user
        super().save_model(request, obj, form, change)

        if obj.descricao_solucao and not obj.data_solucao:  # Preenche automaticamente a data de solução
            from django.utils.timezone import now
            obj.data_solucao = now()
            obj.status = 'Concluído'
            obj.save()
        elif obj.descricao_solucao and obj.data_solucao:
            from django.utils.timezone import now
            obj.data_solucao = now()
            obj.status = 'Concluído'
            obj.save()

    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return ['tipo', 'descricao_problema', 'solicitante', 'servico', 'data_criacao', 'status','descricao_solucao']
        
        elif not request.user.is_superuser:
            return ['solicitante', 'status','descricao_solucao', 'data_solucao', 'executor']
        elif obj and request.user.is_superuser and obj.data_solucao:
            return ['tipo', 'descricao_problema', 'solicitante', 'servico', 'descricao_solucao','data_criacao', 'status','data_solucao','executor']
        
        elif obj and request.user.is_superuser:
            return ['tipo', 'descricao_problema', 'solicitante', 'servico', 'data_criacao', 'status','data_solucao','executor']
        
        elif not obj and request.user.is_superuser:
            return [ 'status','descricao_solucao', 'data_solucao', 'executor']
        return []
    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and request.user.is_superuser and obj.status == 'Aberto':
            obj.status = 'Em Andamento'
            obj.executor = request.user
            obj.save()
            return redirect(request.path)  # Refresh da página após salvar a mudança
        return super().change_view(request, object_id, form_url, extra_context)
   