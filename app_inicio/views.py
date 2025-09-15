from django.shortcuts import render, redirect
from .models import Receta
from django.contrib.auth import authenticate, login
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # crea la sesión
            return redirect("home")  # aquí lo mandas a la página principal
        else:
            messages.error(request, "Usuario o contraseña incorrectos")

    return render(request, "app_inicio/login.html")

@login_required
def home_view(request):
    return render(request, "app_inicio/home.html")

def let_us_cook(request):
    sugerencias = []
    if request.method == "POST":
        ingredientes = request.POST.get("ingredientes", "")
        
        # Dividir en palabras o comas
        lista_ingredientes = [i.strip() for i in ingredientes.replace(",", " ").split() if i.strip()]
        
        # Construir un filtro dinámico con OR
        query = Q()
        for ingr in lista_ingredientes:
            query |= Q(nombre__icontains=ingr) | Q(descripcion__icontains=ingr) | Q(pasos__icontains=ingr)
        
        sugerencias = Receta.objects.filter(query).distinct()[:10]

    return render(request, "app_inicio/letuscook.html", {"sugerencias": sugerencias})

def recetas(request):
    return render(request, "app_inicio/recetas.html")

def receta_search(request):
    query = request.GET.get("q")
    resultados = []
    if query:
        resultados = Receta.objects.filter(nombre__icontains=query)
    return render(request, "app_inicio/receta_search.html", {"resultados": resultados, "query": query})