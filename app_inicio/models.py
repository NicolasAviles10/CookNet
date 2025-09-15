from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class Usuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(unique=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
    
class Receta(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    pasos = models.TextField()
    tiempo_preparacion = models.IntegerField(help_text="Tiempo en minutos")

    def __str__(self):
        return self.nombre