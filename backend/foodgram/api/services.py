import io

import reportlab.rl_config
from django.db.models import Q, Sum
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .serializers import FavoriteRecipeSerializer, ShoppingCartRecipeSerializer
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart)


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
        recipes = Recipe.objects.filter(shoppingcart__user=request.user)
        recipes_with_ingredients = RecipeIngredient.objects.filter(
            recipe__in=recipes)
        ingredients = Ingredient.objects.filter(
            recipeingredient__in=recipes_with_ingredients
            ).distinct()
        summed_amount_ingredients = ingredients.annotate(
            amount_sum=Sum(
                'recipeingredient__amount', filter=Q(
                    recipeingredient__in=recipes_with_ingredients
                )))
        for ingredient in summed_amount_ingredients.all():
            file_content.append(
                        f'{ingredient.name} '
                        f'{ingredient.amount_sum} '
                        f'{ingredient.measurement_unit} '
                        )
        return file_content

    def add_recipe_to_shopping_or_favorite(
            self, model, serializer, request, recipe=None,):
        if model.objects.filter(
                recipe=recipe, user=request.user).exists():
            return Response(
                'Запись уже существует.',
                status=status.HTTP_400_BAD_REQUEST
                )
        model.objects.create(user=request.user, recipe=recipe)
        serializer = serializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def add_recipe_to_user_shopping_cart(self, request, recipe=None, pk=None):
        """Добавляет рецепт в список покупок."""
        return self.add_recipe_to_shopping_or_favorite(
            ShoppingCart,
            ShoppingCartRecipeSerializer,
            request,
            recipe=recipe)

    def add_recipe_to_user_favorite(self, request, recipe=None, pk=None):
        """Добавляет рецепт в избранное."""
        return self.add_recipe_to_shopping_or_favorite(
            Favorite,
            FavoriteRecipeSerializer,
            request,
            recipe=recipe)

    def remove_recipe_to_shopping_or_favorite(
            self, model,
            request,
            recipe=None):
        get_object_or_404(model, recipe=recipe, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
