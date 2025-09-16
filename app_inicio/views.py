from django.shortcuts import render, redirect, get_object_or_404
from .models import Receta
from django.contrib.auth import authenticate, login
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from recipebot import recipebot_agent
from django.core.paginator import Paginator

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
    from django.core.paginator import Paginator
    sugerencias_list = []
    receta_ia = None
    receta_ia_nombre = None
    receta_ia_descripcion = None
    ingredientes = ""
    page_obj = None
    if request.method == "POST":
        ingredientes = request.POST.get("ingredientes", "")
        lista_ingredientes = [i.strip() for i in ingredientes.replace(",", " ").split() if i.strip()]
        query = Q()
        for ingr in lista_ingredientes:
            query |= Q(name__icontains=ingr) | Q(description__icontains=ingr) | Q(ingredients__icontains=ingr) | Q(steps__icontains=ingr)
        sugerencias_list = Receta.objects.filter(query).distinct()
        paginator = Paginator(sugerencias_list, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        if ingredientes:
            receta_ia = recipebot_agent(ingredientes)
            receta_ia_nombre = None
            receta_ia_descripcion = None
            import json
            try:
                recetas = json.loads(receta_ia)
                if isinstance(recetas, list) and len(recetas) > 0:
                    receta_ia_nombre = recetas[0].get('name', '')
                    receta_ia_descripcion = recetas[0].get('description', '')
            except Exception:
                receta_ia_nombre = None
                receta_ia_descripcion = None
    return render(request, "app_inicio/letuscook.html", {
        "page_obj": page_obj,
        "receta_ia": receta_ia,
        "receta_ia_nombre": receta_ia_nombre,
        "receta_ia_descripcion": receta_ia_descripcion,
        "ingredientes": ingredientes
    })

def recetas(request):
    from django.core.paginator import Paginator

    recetas_list = Receta.objects.all()
    paginator = Paginator(recetas_list, 20)  # 20 recetas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "app_inicio/recetas.html", {"page_obj": page_obj})

def receta_search(request):
    query = request.GET.get("q")
    resultados = []
    page_obj = None
    if query:
        resultados_list = Receta.objects.filter(name__icontains=query)
        paginator = Paginator(resultados_list, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    return render(request, "app_inicio/receta_search.html", {"page_obj": page_obj, "query": query})

def detalle_receta(request, id):
    receta = get_object_or_404(Receta, id=id)
    return render(request, "app_inicio/detalle_receta.html", {"receta": receta})