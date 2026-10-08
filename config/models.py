from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class GoogleIdentity(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='google_identity',
    )
    subject = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Google account for {self.user}'


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
