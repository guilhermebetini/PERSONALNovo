import hashlib
import json
import logging
import re
import secrets
import unicodedata
from html.parser import HTMLParser

import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import (
    require_GET,
    require_http_methods,
    require_POST,
)

from .models import Evaluation, GoogleIdentity

logger = logging.getLogger(__name__)


class VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored_tags = []

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style', 'noscript'}:
            self.ignored_tags.append(tag)

    def handle_endtag(self, tag):
        if self.ignored_tags and tag == self.ignored_tags[-1]:
            self.ignored_tags.pop()

    def handle_data(self, data):
        if not self.ignored_tags:
            self.parts.append(data)


SEARCHABLE_PAGES = (
    ('paginaInicial.html', 'Página inicial', '/'),
    ('avaliacao.html', 'Avaliações', '/avaliacao.html'),
    ('avaliar-pratos.html', 'Avaliar pratos', '/avaliar-pratos.html'),
    ('avaliar-atendimento.html', 'Avaliar atendimento', '/avaliar-atendimento.html'),
    ('avaliar-estabelecimento.html', 'Avaliar estabelecimento', '/avaliar-estabelecimento.html'),
    ('contato.html', 'Contato', '/contato.html'),
    ('serviço.html', 'Serviços', '/serviço.html'),
)


def normalize_search_text(value):
    decomposed = unicodedata.normalize('NFD', value.casefold())
    return ''.join(character for character in decomposed if not unicodedata.combining(character))


def make_excerpt(text, terms, limit=240):
    if len(text) <= limit:
        return text
    normalized = normalize_search_text(text)
    match_positions = [normalized.find(term) for term in terms]
    match_positions = [position for position in match_positions if position >= 0]
    start = max(0, (min(match_positions) if match_positions else 0) - limit // 3)
    end = min(len(text), start + limit)
    excerpt = text[start:end].strip()
    if start:
        excerpt = f'…{excerpt}'
    if end < len(text):
        excerpt = f'{excerpt}…'
    return excerpt


def pagina(nome, proteger=False):
    @ensure_csrf_cookie
    def view(request):
        return render(request, nome)

    return login_required(view, login_url='/entrar/') if proteger else view


@require_GET
def search(request):
    query = request.GET.get('q', '').strip()[:100]
    terms = re.findall(r'\w+', normalize_search_text(query))
    results = []

    if terms:
        for filename, title, url in SEARCHABLE_PAGES:
            parser = VisibleTextParser()
            with (settings.BASE_DIR / 'HTML' / filename).open(encoding='utf-8') as page:
                parser.feed(page.read())
            text = ' '.join(' '.join(parser.parts).split())
            searchable_text = normalize_search_text(f'{title} {text}')
            if all(term in searchable_text for term in terms):
                results.append({
                    'title': title,
                    'url': url,
                    'excerpt': make_excerpt(text, terms),
                })

        category_labels = dict(Evaluation.Category.choices)
        evaluations = Evaluation.objects.order_by('-created_at')[:1000]
        matching_evaluations = [
            evaluation
            for evaluation in evaluations
            if all(
                term in normalize_search_text(
                    f'{evaluation.comment} {evaluation.dish_name} {evaluation.category}'
                )
                for term in terms
            )
        ]
        for evaluation in matching_evaluations[:10]:
            title = category_labels.get(evaluation.category, 'Avaliação')
            if evaluation.dish_name:
                title = f'{title}: {evaluation.dish_name}'
            text = evaluation.comment or f'Avaliação com nota {evaluation.rating} de 5.'
            results.append({
                'title': title,
                'url': '/avaliacao.html',
                'excerpt': make_excerpt(text, terms),
            })

    return render(request, 'buscar.html', {
        'query': query,
        'results': results[:20],
    })


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    status_message = ''
    username = ''
    google_nonce = secrets.token_urlsafe(32)
    request.session['google_login_nonce'] = google_nonce
    if request.method == 'POST':
        username = request.POST.get('usuario', '').strip()
        password = request.POST.get('senha', '')
        user = authenticate(request, username=username, password=password)
        if user is None:
            status_message = 'Usuário ou senha inválidos.'
        else:
            login(request, user)
            return redirect('dashboard')

    return render(request, 'entrar.html', {
        'status_message': status_message,
        'username': username,
        'google_client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'google_nonce': google_nonce,
    })


@require_POST
def google_login(request):
    if request.user.is_authenticated:
        return JsonResponse({'redirect_url': reverse('dashboard')})

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'A resposta do Google é inválida.'}, status=400)
    credential = payload.get('credential') if isinstance(payload, dict) else None
    if not isinstance(credential, str) or not credential or len(credential) > 10000:
        return JsonResponse({'error': 'O Google não retornou uma credencial válida.'}, status=400)

    try:
        from google.auth.exceptions import GoogleAuthError
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2 import id_token

        profile = id_token.verify_oauth2_token(
            credential,
            GoogleRequest(),
            audience=settings.GOOGLE_OAUTH_CLIENT_ID,
        )
    except (GoogleAuthError, ValueError, requests.RequestException) as error:
        logger.info('Google sign-in credential validation failed: %s', error)
        return JsonResponse({'error': 'A autenticação do Google falhou. Tente novamente.'}, status=401)
    except ImportError:
        logger.exception('Google authentication dependencies are unavailable.')
        return JsonResponse({'error': 'O login do Google está indisponível no servidor.'}, status=503)

    subject = profile.get('sub')
    email = profile.get('email')
    if not isinstance(subject, str) or not subject or len(subject) > 255:
        return JsonResponse({'error': 'O Google retornou uma conta inválida.'}, status=400)
    nonce = request.session.pop('google_login_nonce', '')
    token_nonce = profile.get('nonce', '')
    if not nonce or not isinstance(token_nonce, str) or not secrets.compare_digest(nonce, token_nonce):
        return JsonResponse({'error': 'A validação do login expirou. Atualize a página e tente novamente.'}, status=401)
    if profile.get('email_verified') is not True:
        return JsonResponse({'error': 'Use uma conta Google com e-mail verificado.'}, status=403)
    if not isinstance(email, str):
        return JsonResponse({'error': 'O Google não retornou um e-mail válido.'}, status=400)
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'error': 'O Google retornou um e-mail inválido.'}, status=400)

    identity = GoogleIdentity.objects.select_related('user').filter(subject=subject).first()
    if identity is not None:
        user = identity.user
    else:
        User = get_user_model()
        username = f'google_{hashlib.sha256(subject.encode()).hexdigest()}'
        display_name = profile.get('name', '')
        if not isinstance(display_name, str):
            display_name = ''
        name_parts = display_name.split(maxsplit=1)
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=name_parts[0][:150] if name_parts else '',
            last_name=name_parts[1][:150] if len(name_parts) > 1 else '',
        )
        GoogleIdentity.objects.create(user=user, subject=subject)

    if not user.is_active:
        return JsonResponse({'error': 'Esta conta está desativada.'}, status=403)

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return JsonResponse({'redirect_url': reverse('dashboard')})


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    status_message = ''
    username = ''
    name = ''
    if request.method == 'POST':
        User = get_user_model()
        username = request.POST.get('usuario', '').strip()
        name = request.POST.get('nome', '').strip()
        password = request.POST.get('senha', '')
        if not 2 <= len(name) <= 150 or not 3 <= len(username) <= 150:
            status_message = 'Informe um nome entre 2 e 150 caracteres e um usuário entre 3 e 150 caracteres.'
        elif User.objects.filter(username__iexact=username).exists():
            status_message = 'Esse nome de usuário já está em uso.'
        else:
            candidate = User(username=username, first_name=name)
            try:
                validate_password(password, user=candidate)
            except ValidationError as error:
                status_message = ' '.join(error.messages)
            else:
                candidate.set_password(password)
                candidate.save()
                messages.success(request, 'Cadastro concluído. Entre com seu usuário e senha.')
                return redirect('entrar')

    return render(request, 'cadastrar.html', {
        'status_message': status_message,
        'username': username,
        'name': name,
    })


@require_POST
def logout_view(request):
    logout(request)
    return redirect('inicio')


def _get_rating_distribution():
    distribution = {}
    rows = Evaluation.objects.values('category', 'rating').annotate(count=Count('id'))
    for row in rows:
        distribution.setdefault(row['category'], {})[row['rating']] = row['count']
    return distribution


@require_http_methods(['GET', 'POST'])
def evaluations_api(request):
    if request.method == 'GET':
        counts = {
            item['category']: item['count']
            for item in Evaluation.objects.values('category').annotate(count=Count('id'))
        }
        category_labels = dict(Evaluation.Category.choices)
        rating_distribution = _get_rating_distribution()
        average_rating = Evaluation.objects.aggregate(average=Avg('rating'))['average']
        top_dishes = (
            Evaluation.objects.filter(category=Evaluation.Category.DISHES)
            .values('dish_id', 'dish_name')
            .annotate(total=Count('id'), average=Avg('rating'))
            .order_by('-total', '-average', 'dish_name')[:10]
        )
        recent_evaluations = Evaluation.objects.all()[:100]
        return JsonResponse({
            'atendimento': counts.get(Evaluation.Category.SERVICE, 0),
            'pratos': counts.get(Evaluation.Category.DISHES, 0),
            'estabelecimento': counts.get(Evaluation.Category.ESTABLISHMENT, 0),
            'total': sum(counts.values()),
            'media_geral': round(average_rating, 1) if average_rating is not None else None,
            'distribuicao_notas': rating_distribution,
            'produtos_mais_avaliados': [
                {
                    'dish_id': dish['dish_id'],
                    'dish_name': dish['dish_name'] or 'Prato sem nome',
                    'total': dish['total'],
                    'media': round(dish['average'], 1),
                }
                for dish in top_dishes
            ],
            'ultimas_avaliacoes': [
                {
                    'id': evaluation.pk,
                    'categoria': evaluation.category,
                    'categoria_label': category_labels.get(evaluation.category, evaluation.category),
                    'prato': evaluation.dish_name,
                    'nota': evaluation.rating,
                    'comentario': evaluation.comment,
                    'criada_em': evaluation.created_at.isoformat(),
                }
                for evaluation in recent_evaluations
            ],
        })

    if request.content_type != 'application/json':
        return JsonResponse({'error': 'Envie os dados da avaliação em JSON.'}, status=415)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Os dados enviados não são um JSON válido.'}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({'error': 'Os dados da avaliação são inválidos.'}, status=400)

    category = payload.get('category')
    if category not in Evaluation.Category.values:
        return JsonResponse({'error': 'Selecione uma categoria de avaliação válida.'}, status=400)

    rating = payload.get('rating')
    if isinstance(rating, bool) or not isinstance(rating, int):
        return JsonResponse({'error': 'Informe uma nota entre 1 e 5.'}, status=400)
    if not 1 <= rating <= 5:
        return JsonResponse({'error': 'Informe uma nota entre 1 e 5.'}, status=400)

    comment = payload.get('comment', '')
    dish_id = payload.get('dishId', '')
    dish_name = payload.get('dishName', '')
    if not all(isinstance(value, str) for value in (comment, dish_id, dish_name)):
        return JsonResponse({'error': 'Os campos de texto da avaliação são inválidos.'}, status=400)
    if len(comment) > 500 or len(dish_id) > 100 or len(dish_name) > 80:
        return JsonResponse({'error': 'Um ou mais campos excedem o tamanho permitido.'}, status=400)
    if category == Evaluation.Category.DISHES and not dish_id:
        return JsonResponse({'error': 'Selecione o prato que deseja avaliar.'}, status=400)

    evaluation = Evaluation.objects.create(
        category=category,
        rating=rating,
        comment=comment.strip(),
        dish_id=dish_id,
        dish_name=dish_name.strip(),
    )
    return JsonResponse({'id': evaluation.pk, 'message': 'Avaliação registrada.'}, status=201)
