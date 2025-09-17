from .forms import FavoritosForm
from .models import UsuarioFavorito
from django.contrib.auth.decorators import login_required
# Vista para seleccionar favoritos
@login_required
def seleccionar_favoritos(request):
    user = request.user
    favoritos_existentes = UsuarioFavorito.objects.filter(user=user).values_list('receta_id', flat=True)
    favoritos_objs = UsuarioFavorito.objects.filter(user=user).select_related('receta')
    favoritos_recetas = [f.receta for f in favoritos_objs]
    favoritos_ids = set(r.id for r in favoritos_recetas)
    search_query = None
    search_results = []
    if request.method == 'POST':
        search_query = request.POST.get('search', '').strip()
        if search_query:
            search_results = Receta.objects.filter(name__icontains=search_query)[:10]
        receta_id = request.POST.get('add_fav')
        if receta_id and len(favoritos_recetas) < 5 and int(receta_id) not in favoritos_ids:
            receta = Receta.objects.get(id=receta_id)
            UsuarioFavorito.objects.get_or_create(user=user, receta=receta)
            return redirect('seleccionar_favoritos')
        remove_id = request.POST.get('remove_fav')
        if remove_id:
            UsuarioFavorito.objects.filter(user=user, receta_id=remove_id).delete()
            return redirect('seleccionar_favoritos')
    return render(request, 'app_inicio/seleccionar_favoritos.html', {
        'favoritos_recetas': favoritos_recetas,
        'search_query': search_query,
        'search_results': search_results,
        'favoritos_max': len(favoritos_recetas) >= 5,
        'favoritos_ids': favoritos_ids
    })

from django.shortcuts import render, redirect, get_object_or_404
from .models import Receta
from django.contrib.auth import authenticate, login
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from recipebot import recipebot_agent
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserCreationForm

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
    receta_ia_razon = None
    receta_ia_descripcion = None
    ingredientes = ""
    page_obj = None
    if request.method == "POST":
        ingredientes = request.POST.get("ingredientes", "")
        lista_ingredientes = [i.strip() for i in ingredientes.replace(",", " ").split() if i.strip()]
        query = Q()
        for ingr in lista_ingredientes:
            query |= Q(name__icontains=ingr) | Q(description__icontains=ingr) | Q(ingredients__icontains=ingr) | Q(steps__icontains=ingr)
        sugerencias_list = Receta.objects.filter(query).distinct()[:7]
        paginator = Paginator(sugerencias_list, 7)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        if ingredientes:
            receta_ia = recipebot_agent(ingredientes, user=request.user if request.user.is_authenticated else None)
            receta_ia_nombre = None
            receta_ia_razon = None
            import json
            try:
                recetas = json.loads(receta_ia)
                if isinstance(recetas, list) and len(recetas) > 0:
                    receta_ia_nombre = recetas[0].get('name', '')
                    receta_ia_razon = recetas[0].get('razon', '')
                elif isinstance(recetas, dict):
                    receta_ia_nombre = recetas.get('name', '')
                    receta_ia_razon = recetas.get('razon', '')
            except Exception:
                receta_ia_nombre = None
                receta_ia_razon = None
    return render(request, "app_inicio/letuscook.html", {
        "page_obj": page_obj,
        "receta_ia": receta_ia,
        "receta_ia_nombre": receta_ia_nombre,
    "receta_ia_razon": receta_ia_razon,
        "ingredientes": ingredientes
    })

def recetas(request):
    from django.core.paginator import Paginator
    from .models import Receta, UsuarioFavorito
    recetas_list = Receta.objects.all()
    paginator = Paginator(recetas_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    favoritos_ids = set()
    if request.user.is_authenticated:
        favoritos_ids = set(UsuarioFavorito.objects.filter(user=request.user).values_list('receta_id', flat=True))
        if request.method == 'POST':
            receta_id = request.POST.get('add_fav')
            if receta_id and int(receta_id) not in favoritos_ids and len(favoritos_ids) < 5:
                receta = Receta.objects.get(id=receta_id)
                UsuarioFavorito.objects.get_or_create(user=request.user, receta=receta)
                favoritos_ids.add(int(receta_id))
    return render(request, "app_inicio/recetas.html", {"page_obj": page_obj, "favoritos_ids": favoritos_ids})

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
    receta_traducida = receta
    es_favorito = False
    pasos_list = []
    import ast
    try:
        if receta_traducida.steps and receta_traducida.steps.strip().startswith('['):
            pasos_list = ast.literal_eval(receta_traducida.steps)
        else:
            pasos_list = [receta_traducida.steps]
    except Exception:
        pasos_list = [receta_traducida.steps]
    if request.user.is_authenticated:
        from .models import UsuarioFavorito
        es_favorito = UsuarioFavorito.objects.filter(user=request.user, receta=receta).exists()
        if request.method == "POST" and not es_favorito:
            UsuarioFavorito.objects.get_or_create(user=request.user, receta=receta)
            es_favorito = True
    return render(request, "app_inicio/detalle_receta.html", {"receta": receta_traducida, "es_favorito": es_favorito, "pasos_list": pasos_list})

def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # guarda el usuario en auth_user
            username = form.cleaned_data.get("username")
            messages.success(request, f"Usuario {username} creado con éxito. ¡Ya puedes iniciar sesión!")
            return redirect("login")  # redirige al login
    else:
        form = UserCreationForm()
    return render(request, "app_inicio/register.html", {"form": form})