import json

from django.db.models import Avg, Count
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.shortcuts import render

from .models import Evaluation


def pagina(nome):
    @ensure_csrf_cookie
    def view(request):
        return render(request, nome)

    return view


@require_http_methods(['GET', 'POST'])
def evaluations_api(request):
    if request.method == 'GET':
        counts = {
            item['category']: item['count']
            for item in Evaluation.objects.values('category').annotate(count=Count('id'))
        }
        category_labels = dict(Evaluation.Category.choices)
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
