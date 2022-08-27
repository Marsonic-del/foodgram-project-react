import io

import reportlab.rl_config
from django.db.models import Q, Sum
from recipes.models import (Favorites, Ingredient, Recipe, RecipesIngredients,
                            Shopping_cart)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from .serializers import (FavoritesRecipeSerializer,
                          Shopping_cartRecipeSerializer)


def get_pdf_file(content: list):
    """Из строк списка формирует PDF file."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    reportlab.rl_config.warnOnMissingFontGlyphs = 0
    pdfmetrics.registerFont(
        TTFont('DejaVuSans', 'static/fonts/DejaVuSans.ttf')
        )
    c.setFont('DejaVuSans', 10)
    bottom = 800
    for string in content:
        c.drawString(22, bottom, string)
        bottom -= 20
    c.save()
    buffer.seek(0)
    return buffer


class ViewsetForRecipes(viewsets.ModelViewSet):
    """Вюсет для модели Recipe."""

    def get_shopping_cart_content(self, request, pk=None):
        """Формирует контент с ингредиентами для списка покупок."""
        file_content = ['Не забыть купить:']
        recipes = Recipe.objects.filter(shopping_cart__owner=request.user)
        recipes_with_ingredients = RecipesIngredients.objects.filter(
            recipe__in=recipes)
        ingredients = Ingredient.objects.filter(
            recipesingredients__in=recipes_with_ingredients
            ).distinct()
        summed_amount_ingredients = ingredients.annotate(
            amount_sum=Sum(
                'recipesingredients__amount', filter=Q(
                    recipesingredients__in=recipes_with_ingredients
                )))
        for ingredient in summed_amount_ingredients.all():
            file_content.append(
                        f'{ingredient.name} '
                        f'{ingredient.amount_sum} '
                        f'{ingredient.measurement_unit} '
                        )
        return file_content

    def add_recipe_to_user_shopping_cart(self, request, recipe=None, pk=None):
        """Добавляет рецепт в список покупок."""
        if Shopping_cart.objects.filter(
                                 recipe=recipe, owner=request.user
                                 ).exists():
            raise ValidationError(
                detail={'Список покупок': 'Запись уже существует.'}
                )
        Shopping_cart.objects.create(owner=request.user, recipe=recipe)
        serializer = Shopping_cartRecipeSerializer(recipe)
        return serializer

    def add_recipe_to_user_favorites(self, request, recipe=None, pk=None):
        """Добавляет рецепт в избранное."""
        if Favorites.objects.filter(recipe=recipe).exists():
            raise ValidationError(
                detail={'Избранное': 'Запись уже существует.'}
                )
        Favorites.objects.create(user=request.user,
                                 recipe=recipe)
        serializer = FavoritesRecipeSerializer(recipe)
        return serializer
