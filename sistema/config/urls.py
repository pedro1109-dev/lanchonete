from django.contrib import admin
from django.contrib.auth import views as auth
from django.urls import path
from core import views
urlpatterns=[path('',views.index),path('admin/',admin.site.urls),path('login/',auth.LoginView.as_view(template_name='registration/login.html')),path('logout/',auth.LogoutView.as_view()),path('health/',views.health),path('api/catalogo/',views.catalogo),path('api/pedidos/',views.pedidos),path('api/pedidos/<int:pk>/status/',views.status),path('api/pedidos/<int:pk>/avaliacao/',views.avaliacao),path('api/relatorio/',views.relatorio)]
