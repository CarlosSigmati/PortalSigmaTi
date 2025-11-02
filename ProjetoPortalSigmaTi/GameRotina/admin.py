from django.contrib import admin
from .models import PlayerProgress, Rotina, Badge

# ==============================
# Admin para Badge
# ==============================
@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'icone', 'descricao')
    search_fields = ('nome',)
    list_filter = ('nome',)

# ==============================
# Admin para Rotina
# ==============================
@admin.register(Rotina)
class RotinaAdmin(admin.ModelAdmin):
    list_display = ('user', 'data_hora', 'pontos', 'tarefas_concluidas')
    search_fields = ('user__username',)
    list_filter = ('data_hora',)
    readonly_fields = ('pontos',)
    ordering = ('-data_hora',)

    def tarefas_concluidas(self, obj):
        # Lista de tarefas concluídas
        tarefas = []
        if obj.leitura: tarefas.append('📖 Leitura')
        if obj.arte_marcial: tarefas.append('🥋 Arte Marcial')
        if obj.limpar_casa: tarefas.append('🧹 Limpar Casa')
        if obj.musculacao: tarefas.append('🏋️ Musculação')
        if obj.alimentacao_saudavel: tarefas.append('🥗 Alimentação Saudável')
        # Contabiliza meta de água
        if getattr(obj, 'copos_agua', 0) >= 8:
            tarefas.append('💧 Água (meta atingida)')
        return ', '.join(tarefas)
    tarefas_concluidas.short_description = 'Tarefas Concluídas'

# ==============================
# Admin para PlayerProgress
# ==============================
@admin.register(PlayerProgress)
class PlayerProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'nivel', 'pontos_totais', 'streak', 'ultima_atualizacao')
    search_fields = ('user__username',)
    list_filter = ('nivel',)
    readonly_fields = ('pontos_totais', 'nivel', 'streak')

    def ultima_atualizacao(self, obj):
        ultima = Rotina.objects.filter(user=obj.user).order_by('-data_hora').first()
        return ultima.data_hora if ultima else 'Nunca'
    ultima_atualizacao.short_description = 'Última Atualização'
