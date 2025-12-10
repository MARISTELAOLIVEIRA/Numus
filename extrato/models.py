from django.db import models
from perfil.models import Categorias, Conta
from django.contrib.auth.models import User

class Valores(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    choice_tipo = (
        ('E', 'Entrada'),
        ('S', 'Saída')
    )
    
    valor = models.FloatField()
    categoria = models.ForeignKey(Categorias, on_delete=models.DO_NOTHING, blank=True, null=True)
    descricao = models.TextField()
    data = models.DateField()
    conta = models.ForeignKey(Conta, on_delete=models.DO_NOTHING)
    tipo = models.CharField(max_length=1, choices=choice_tipo)

    def __str__(self):
        return self.descricao
