from django.db import models
from datetime import datetime
from django.contrib.auth.models import User

class Categorias(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    categoria = models.CharField(max_length=50)
    essencial = models.BooleanField(default=False)
    valor_planejado = models.FloatField()
    
    def __str__(self):
        return self.categoria
    
    def total_gasto(self):
        from extrato.models import Valores
        valores = Valores.objects.filter(categoria__id=self.id, user=self.user).filter(data__month=datetime.now().month)
        total_valor = 0
        for valor in valores:
            total_valor += valor.valor
        return total_valor

    def calcula_percentual_gasto_por_categoria(self):
        
        try:
            return int((self.total_gasto() * 100) / self.valor_planejado)
        except:
            return 0
        

class Conta(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    banco_choices = (
        ('NU', 'Nubank'),
        ('CE', 'Caixa econômica'),
        ('ST', 'Santander'),
        ('BB', 'Banco do Brasil')
    )

    tipo_choices = (
        ('pf', 'Pessoa física'),
        ('pj', 'Pessoa jurídica'),
    )

    apelido = models.CharField(max_length=50)
    banco = models.CharField(max_length=2, choices=banco_choices)
    tipo = models.CharField(max_length=2, choices=tipo_choices)
    valor = models.FloatField()
    icone = models.ImageField(upload_to='icones', blank=True, null=True)

    def __str__(self):
        return self.apelido


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    foto_perfil = models.ImageField(upload_to='perfis', blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    # Configurações do usuário
    idioma = models.CharField(max_length=10, blank=True, null=True, default='pt-BR')
    moeda = models.CharField(max_length=5, blank=True, null=True, default='BRL')
    formato_data = models.CharField(max_length=12, blank=True, null=True, default='dd/mm/yyyy')
    notificacoes_email = models.BooleanField(default=True)
    tema = models.CharField(max_length=10, blank=True, null=True, default='system')
    auto_categoria = models.BooleanField(default=True)
    layout_dashboard = models.CharField(max_length=20, blank=True, null=True, default='comfortable')
    two_factor_enabled = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Perfil de {self.user.username}"