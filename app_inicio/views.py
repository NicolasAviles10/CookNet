from django.shortcuts import render

def login_view(request):
    return render(request, "app_inicio/login.html")

def home_view(request):
    return render(request, "app_inicio/home.html")
