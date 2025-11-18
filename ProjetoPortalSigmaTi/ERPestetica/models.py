from django.db import models
from django.utils import timezone
from datetime import timedelta



class HorarioFuncionamento(models.Model):
    DIAS_SEMANA = [
        (0, "Segunda-feira"),
        (1, "Terça-feira"),
        (2, "Quarta-feira"),
        (3, "Quinta-feira"),
        (4, "Sexta-feira"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    loja = models.ForeignKey('Loja', on_delete=models.CASCADE, related_name='horarios')
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_abertura = models.TimeField()
    hora_fechamento = models.TimeField()

    class Meta:
        unique_together = ('loja', 'dia_semana')
        ordering = ['dia_semana']

    def __str__(self):
        return f"{self.get_dia_semana_display()} - {self.loja.nome}: {self.hora_abertura} às {self.hora_fechamento}"



class Loja(models.Model):
    nome = models.CharField(max_length=100)
    endereco = models.CharField(max_length=200)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    hora_abertura = models.TimeField(default="08:00")
    hora_fechamento = models.TimeField(default="18:00")

    def __str__(self):
        return self.nome


class Profissional(models.Model):
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name="profissionais")
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    servicos = models.ManyToManyField('Servico', related_name='profissionais')

    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} ({self.loja.nome})"


class Cliente(models.Model):
    loja = models.ForeignKey('Loja', on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=150)
    telefone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    data_cadastro = models.DateTimeField(default=timezone.now)
    observacoes = models.TextField(blank=True)
    
    def __str__(self):
        loja_nome = self.loja.nome if self.loja else "Sem loja"
        return f"{self.nome} ({loja_nome})"


class Servico(models.Model):
    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    duracao_minutos = models.PositiveIntegerField(default=30)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} ({self.duracao_minutos} min)"


class Agendamento(models.Model):
    id = models.AutoField(primary_key=True)

    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("confirmado", "Confirmado"),
        ("cancelado", "Cancelado"),
        ("concluido", "Concluído"),
    ]

    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="agendamentos"
    )
    loja = models.ForeignKey(
        Loja, on_delete=models.CASCADE, related_name="agendamentos"
    )
    
    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        related_name="agendamentos",
        null=True,
        blank=True
    )

    servicos = models.ManyToManyField(Servico, related_name="agendamentos")

    data_hora = models.DateTimeField()
    duracao_minutos = models.PositiveIntegerField(blank=True, null=True)
    observacoes = models.TextField(blank=True)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pendente"
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_hora"]
        #unique_together = ("loja", "data_hora", "cliente")

    def __str__(self):
        return f"{self.cliente.nome} — {self.data_hora.strftime('%d/%m/%Y %H:%M')} ({self.get_status_display()})"

    def calcular_duracao(self):
        """Retorna a duração em minutos. Só soma serviços se houver id (objeto salvo)."""
        if self.duracao_minutos:
            return self.duracao_minutos
        if self.pk:  # só soma se o objeto já existe no banco
            return sum(s.duracao_minutos for s in self.servicos.all())
        return 0  # ou algum valor padrão se ainda não houver id

    @property
    def hora_fim(self):
        return self.data_hora + timedelta(minutes=self.calcular_duracao())

    def save(self, *args, **kwargs):
        """Salva o agendamento, atualizando duracao_minutos se necessário."""
        super().save(*args, **kwargs)  # salva primeiro para ter o id
        if not self.duracao_minutos and self.servicos.exists():
            self.duracao_minutos = self.calcular_duracao()
            super().save(update_fields=["duracao_minutos"])