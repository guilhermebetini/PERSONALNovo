from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Evaluation(models.Model):
    class Category(models.TextChoices):
        DISHES = 'pratos', 'Pratos'
        SERVICE = 'atendimento', 'Atendimento'
        ESTABLISHMENT = 'estabelecimento', 'Estabelecimento'

    category = models.CharField(max_length=20, choices=Category.choices, db_index=True)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.CharField(max_length=500, blank=True)
    dish_id = models.CharField(max_length=100, blank=True)
    dish_name = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
