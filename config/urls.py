"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from .views import pagina

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', pagina('paginaInicial.html'), name='inicio'),
    path('paginaInicial.html', pagina('paginaInicial.html'), name='pagina-inicial'),
    path('index.guilherme.html', pagina('paginaInicial.html'), name='index-legado'),
    path('avaliacao.html', pagina('avaliacao.html'), name='avaliacao'),
    path('avaliçao.html', pagina('avaliacao.html'), name='avaliacao-legado'),
    path('contato.html', pagina('contato.html'), name='contato'),
    path('cadastrar.html', pagina('cadastrar.html'), name='cadastrar'),
    path('serviço.html', pagina('serviço.html'), name='servico'),
    path('dashboard.html', pagina('dashboard.html'), name='dashboard'),
    path('entrar.html', pagina('cadastrar.html'), name='entrar'),
    path('produtos.html', pagina('serviço.html'), name='produtos'),
]
