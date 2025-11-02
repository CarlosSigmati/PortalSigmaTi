from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Badge(models.Model):
    nome = models.CharField(max_length=50)
    icone = models.CharField(max_length=5)
    descricao = models.CharField(max_length=200, blank=True)
    requisito_pontos = models.IntegerField(default=0)
    requisito_streak = models.IntegerField(default=0)

    def __str__(self):
        return self.nome


class PlayerProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pontos_totais = models.IntegerField(default=0)
    nivel = models.IntegerField(default=1)
    streak = models.IntegerField(default=0)
    ultimo_checkin = models.DateField(null=True, blank=True)
    badges = models.ManyToManyField(Badge, blank=True)
    
    @property
    def xp_proximo_nivel(self):
        """XP faltando para o próximo nível"""
        return 100 - (self.pontos_totais % 100)

    def calcular_nivel(self):
        """Cada 100 pontos = +1 nível"""
        self.nivel = (self.pontos_totais // 100) + 1
        return self.nivel

    def atualizar_streak(self):
        """Atualiza streak com base na data de hoje."""
        hoje = timezone.now().date()
        if self.ultimo_checkin:
            delta = (hoje - self.ultimo_checkin).days
            if delta == 1:
                self.streak += 1
            elif delta > 1:
                self.streak = 1
        else:
            self.streak = 1
        self.ultimo_checkin = hoje
        self.save()

    def verificar_conquistas(self):
        """Verifica conquistas automaticamente."""
        for badge in Badge.objects.all():
            if (self.pontos_totais >= badge.requisito_pontos and 
                self.streak >= badge.requisito_streak):
                self.badges.add(badge)
        self.save()

    def __str__(self):
        return f"{self.user.username} (Lvl {self.nivel})"


class Rotina(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    data_hora = models.DateTimeField(auto_now_add=True)  # datetime
    leitura = models.BooleanField(default=False)
    arte_marcial = models.BooleanField(default=False)
    limpar_casa = models.BooleanField(default=False)
    musculacao = models.BooleanField(default=False)
    alimentacao_saudavel = models.BooleanField(default=False)
    # Novo campo
    copos_agua = models.PositiveIntegerField(default=0)  # número de copos de 250ml
    enviado = models.BooleanField(default=False)
    pontos = models.PositiveIntegerField(default=0)

    def tarefas_concluidas(self):
        tarefas = [
            self.leitura,
            self.arte_marcial,
            self.limpar_casa,
            self.musculacao,
            self.alimentacao_saudavel
        ]
        # Considera meta de água
        if self.copos_agua >= 8:
            tarefas.append(True)
        return sum(tarefas)

    def calcular_pontos(self):
        self.pontos = self.tarefas_concluidas() * 10
        return self.pontos
