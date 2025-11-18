from django.db import models


class Anamnese(models.Model):
    # ----------------------------
    # DADOS PESSOAIS
    # ----------------------------
    nome = models.CharField(max_length=150)
    data_nascimento = models.DateField(null=True, blank=True)
    idade = models.IntegerField(null=True, blank=True)
    sexo = models.CharField(max_length=20, choices=[
        ("M", "Masculino"),
        ("F", "Feminino"),
        ("Outro", "Outro"),
    ], blank=True)

    estado_civil = models.CharField(max_length=50, blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(max_length=150, blank=True)
    profissao = models.CharField(max_length=150, blank=True)
    origem_encaminhamento = models.CharField(max_length=200, blank=True)

    # ----------------------------
    # RESPONSÁVEL (MENOR DE IDADE)
    # ----------------------------
    responsavel_nome = models.CharField(max_length=150, blank=True)
    responsavel_rg = models.CharField(max_length=50, blank=True)
    responsavel_cpf = models.CharField(max_length=50, blank=True)

    # ----------------------------
    # MOTIVO DA CONSULTA
    # ----------------------------
    motivo_consulta = models.TextField(blank=True)
    tempo_problema = models.CharField(max_length=100, blank=True)
    fez_tratamento = models.BooleanField(default=False)
    tratamento_local = models.CharField(max_length=200, blank=True)
    expectativas = models.TextField(blank=True)

    # ----------------------------
    # HISTÓRICO MÉDICO GERAL
    # ----------------------------
    tratamento_medico = models.BooleanField(default=False)
    tratamento_medico_qual = models.CharField(max_length=200, blank=True)

    usa_medicamentos = models.BooleanField(default=False)
    medicamentos_detalhes = models.TextField(blank=True)

    usa_suplementos = models.BooleanField(default=False)
    suplementos_quais = models.TextField(blank=True)

    alergias = models.BooleanField(default=False)
    alergias_quais = models.TextField(blank=True)

    condicoes_saude = models.TextField(
        blank=True,
        help_text="Lista como: Hipertensão; Diabetes; Doença Cardiovascular..."
    )

    data_ultimo_exame = models.DateField(null=True, blank=True)
    hospitalizado = models.BooleanField(default=False)
    hospitalizado_detalhes = models.TextField(blank=True)

    fumante = models.BooleanField(default=False)
    fumo_quantidade_tempo = models.CharField(max_length=200, blank=True)

    alcool = models.BooleanField(default=False)
    alcool_frequencia = models.CharField(max_length=200, blank=True)

    drogas = models.BooleanField(default=False)
    drogas_quais_frequencia = models.TextField(blank=True)

    # ----------------------------
    # ASSINATURAS E DECLARAÇÕES
    # ----------------------------
    assinatura_paciente = models.ImageField(upload_to="assinaturas/", blank=True, null=True)
    data_assinatura_paciente = models.DateField(null=True, blank=True)

    assinatura_responsavel = models.ImageField(upload_to="assinaturas/", blank=True, null=True)
    data_assinatura_responsavel = models.DateField(null=True, blank=True)

    # Registro automático
    data_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} - {self.data_envio.strftime('%d/%m/%Y %H:%M')}"
