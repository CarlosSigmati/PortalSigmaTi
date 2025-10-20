from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now

class LinkUtil(models.Model):
    nome = models.CharField(max_length=100)
    url = models.URLField()

    def __str__(self):
        return self.nome

class Contato(models.Model):
    TIPOS_CHOICES = [
        ('Parceria', 'Parceria'),
        ('Fornecedor', 'Fornecedor'),
        ('colaborador', 'Colaborador'),
        ('cliente', 'Cliente'),
        ('prospeccao', 'Prospeccao'),
    ]
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=15, unique=True)  # Número de telefone
    empresa = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS_CHOICES)

    def __str__(self):
        return f"{self.nome} - {self.telefone}"

class Cliente(models.Model):
    TIPO_CHOICES = [
        ('freelancer', 'Freelancer'),
        ('fixo', 'Fixo (Contrato)')
    ]

    nome = models.CharField(max_length=100)
    cpf_cnpj = models.CharField(max_length=18, unique=True)
    contato = models.ForeignKey('Contato', on_delete=models.CASCADE, null=False, default='')
    email = models.EmailField(unique=True)
    data_contrato = models.DateField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    observacao = models.TextField(blank=True, null=True)

    # ✅ Novo campo: Usuários responsáveis
    usuarios_responsaveis = models.ManyToManyField(
        User,
        blank=True,
        related_name='clientes_responsaveis',
        verbose_name='Usuários Responsáveis'
    )

    def __str__(self):
        return self.nome

    def listar_responsaveis(self):
        return ", ".join([user.username for user in self.usuarios_responsaveis.all()])

class Servico(models.Model):
    CATEGORIAS = [
        ('infraestrutura', 'Infraestrutura'),
        ('desenvolvimento', 'Desenvolvimento'),
        ('automacao', 'Automação'),
        ('suporte', 'Suporte'),
        ('consultoria', 'Consultoria'),
    ]

    MODELOS_COBRANCA = [
        ('hora', 'Hora'),
        ('projeto_fechado', 'Projeto Fechado'),
        ('mensalidade', 'Mensalidade'),
        ('retainer', 'Retainer'),
    ]

    REQUISITOS = [
        ('acesso_a_conta', 'Acesso a Conta'),
        ('acesso_remoto', 'Acesso Remoto'),
        ('documentacao_rede', 'Documentação da Rede'),
        ('acesso_servidor', 'Acesso ao Servidor'),
        ('infraestrutura_basica', 'Infraestrutura Básica'),
        ('equipamento_rede', 'Equipamento de Rede'),
    ]

    FERRAMENTAS = [
        ('AnyDesk', 'AnyDesk'),
        ('pendrive', 'PenDrive'),
        ('powerapps', 'PowerApps'),
        ('python', 'Python'),
        ('django', 'Django'),
        ('react', 'React'),
        ('pfsense', 'Pfsense'),
        ('mikrotik', 'Mikrotik'),
        ('power_apps', 'Power Apps'),
        ('github', 'GitHub'),
        ('azure', 'Azure'),
        ('aws', 'AWS'),
        ('docker', 'Docker'),
        ('sql_server', 'SQL Server'),
    ]

    TEMPO_MEDIO = [
        ('30_minutos','30 minutos'),
        ('1_hora','1 hora'),
        ('3_horas','3 horas'),
        ('6_horas','6 horas'),
        ('12_horas','12 horas'),
        ('1_dia_util', '1 dia útil'),
        ('3_dias_uteis', '3 dias úteis'),
        ('5_dias_uteis', '5 dias úteis'),
        ('1_semana', '1 semana'),
        ('2_semanas', '2 semanas'),
        ('1_mes', '1 mês'),
    ]

    COMPLEXIDADE = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
    ]

    STATUS = [
        ('ativo', 'Ativo'),
        ('em_desenvolvimento', 'Em Desenvolvimento'),
        ('sob_demanda', 'Sob Demanda'),
        ('em_manutencao', 'Em Manutenção'),
    ]

    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, default='hora')
    modelo_cobranca = models.CharField(max_length=50, choices=MODELOS_COBRANCA)
    requisitos = models.CharField(max_length=100, choices=REQUISITOS, blank=True, null=True)
    ferramentas = models.CharField(max_length=100, choices=FERRAMENTAS, blank=True, null=True)
    tempo_medio_execucao = models.CharField(max_length=50, choices=TEMPO_MEDIO)
    nivel_complexidade = models.CharField(max_length=50, choices=COMPLEXIDADE)
    status = models.CharField(max_length=50, choices=STATUS)
    documentacao = models.FileField(upload_to='documentos/', blank=True, null=True)

    def __str__(self):
        return self.nome

class Demanda(models.Model):
    # Tipos
    CHAMADO = 'Chamado'
    PROJETO = 'Projeto'
    TIPO_CHOICES = [
        (CHAMADO, 'Chamado'),
        (PROJETO, 'Projeto'),
    ]

    # Status
    ABERTO = 'Aberto'
    EM_ANDAMENTO = 'Em Andamento'
    CONCLUIDO = 'Concluído'
    STATUS_CHOICES = [
        (ABERTO, 'Aberto'),
        (EM_ANDAMENTO, 'Em Andamento'),
        (CONCLUIDO, 'Concluído'),
    ]

    # Campos principais
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demandas_solicitadas')
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default=CHAMADO)
    descricao_problema = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ABERTO)
    executor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demandas_resolvidas', null=True, blank=True)
    descricao_solucao = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_verificacao = models.DateTimeField(blank=True, null=True) 
    data_solucao = models.DateTimeField(blank=True, null=True)

    # 🔹 Campos TAP (Projeto)
    objetivo = models.TextField(blank=True, null=True)
    escopo = models.TextField(blank=True, null=True)
    justificativa = models.TextField(blank=True, null=True)
    riscos = models.TextField(blank=True, null=True)
    prazos = models.CharField(max_length=255, blank=True, null=True)
    orcamento = models.CharField(max_length=255, blank=True, null=True)
    responsaveis = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Atualiza status automaticamente
        if self.descricao_solucao and not self.data_solucao:
            self.status = self.CONCLUIDO
            self.data_solucao = now()
        elif not self.descricao_solucao and self.status == self.CONCLUIDO:
            self.status = self.EM_ANDAMENTO
            self.data_solucao = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo} - {self.servico} ({self.status})"
    
#armazenando logs de envio de mensagens para o Telegram
class TelegramLog(models.Model):
    data_envio = models.DateTimeField(default=now)
    destinatario = models.CharField(max_length=100)
    mensagem = models.TextField()
    sucesso = models.BooleanField(default=True)
    erro = models.TextField(blank=True, null=True)