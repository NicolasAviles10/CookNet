from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from app_inicio import views  # o como se llame tu app

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", views.login_view, name="login"),
    path("home/", views.home_view, name="home"),
    path("", lambda request: redirect("login")),
    path("recetas/", views.recetas, name="recetas"),
    path("letuscook/", views.let_us_cook, name="letuscook"),
    path("recetas/search/", views.receta_search, name="receta_search"),
    path("recetas/<int:id>/", views.detalle_receta, name="detalle_receta"),


]
