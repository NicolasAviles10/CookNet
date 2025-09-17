from django.contrib.auth.models import User
from django.db import models
from django.conf import settings


# Create your models here.
class Usuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(unique=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
    
class Receta(models.Model):
    name = models.CharField(max_length=255)
    receta_id = models.IntegerField(unique=True)
    minutes = models.IntegerField()
    contributor_id = models.IntegerField()
    submitted = models.DateField()
    tags = models.TextField(blank=True, null=True)
    nutrition = models.TextField(blank=True, null=True)
    n_steps = models.IntegerField()
    steps = models.TextField()
    description = models.TextField(blank=True, null=True)
    ingredients = models.TextField()
    n_ingredients = models.IntegerField()

    def __str__(self):
        return self.name
    
class UsuarioFavorito(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)

class RegistroComida(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE)
    fecha = models.DateField()
    comida = models.CharField(max_length=20, choices=[('desayuno', 'Desayuno'), ('almuerzo', 'Almuerzo'), ('cena', 'Cena')])
