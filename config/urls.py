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

from .views import (
    evaluations_api,
    google_login,
    login_view,
    logout_view,
    pagina,
    register_view,
    search,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/avaliacoes/', evaluations_api, name='avaliacoes-api'),
    path('buscar/', search, name='buscar'),
    path('', pagina('paginaInicial.html'), name='inicio'),
    path('paginaInicial.html', pagina('paginaInicial.html'), name='pagina-inicial'),
    path('index.guilherme.html', pagina('paginaInicial.html'), name='index-legado'),
    path('avaliacao.html', pagina('avaliacao.html'), name='avaliacao'),
    path('avaliar-pratos.html', pagina('avaliar-pratos.html'), name='avaliar-pratos'),
    path('avaliar-atendimento.html', pagina('avaliar-atendimento.html'), name='avaliar-atendimento'),
    path('avaliar-estabelecimento.html', pagina('avaliar-estabelecimento.html'), name='avaliar-estabelecimento'),
    path('avaliçao.html', pagina('avaliacao.html'), name='avaliacao-legado'),
    path('contato.html', pagina('contato.html'), name='contato'),
    path('cadastrar/', register_view, name='cadastrar'),
    path('cadastrar.html', register_view, name='cadastrar-legacy'),
    path('entrar/', login_view, name='entrar'),
    path('entrar.html', login_view, name='entrar-legacy'),
    path('auth/google/', google_login, name='google-login'),
    path('sair/', logout_view, name='sair'),
    path('serviço.html', pagina('serviço.html'), name='servico'),
    path('dashboard.html', pagina('dashboard.html', proteger=True), name='dashboard'),
    path('dashboard-avaliacoes.html', pagina('dashboard-avaliacoes.html', proteger=True), name='dashboard-avaliacoes'),
    path('produtos.html', pagina('serviço.html'), name='produtos'),
]
