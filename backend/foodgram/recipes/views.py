import imp
import json
from email import message

from api.permissions import RecipePermissions
from api.serializers import (FavoritesRecipeSerializer, IngredientSerializer,
                             RecipeSerializer, ResponseRecipeSerializer,
                             Shopping_cartRecipeSerializer, TagSerializer,
                             UserSerializer)
from django import http
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.db.models import Q, Sum
from django.http import HttpResponseNotFound
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from .models import (Favorites, Ingredient, Recipe, RecipesIngredients,
                     Shopping_cart, Tag)

User = get_user_model()

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None

class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    permission_classes = (RecipePermissions,)
    pagination_class = LimitOffsetPagination

    @action(detail=False, methods=['get',], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request, pk=None):
        file_content = 'Не забыть купить: '
        recipes = Recipe.objects.filter(shopping_cart__owner=request.user)
        recipes_with_ingredients = RecipesIngredients.objects.filter(recipe__in=recipes)
        ingredients = Ingredient.objects.filter(recipesingredients__in=recipes_with_ingredients).distinct()
        ins = ingredients.annotate(amount_sum=Sum('recipesingredients__amount', filter=Q(
            recipesingredients__in=recipes_with_ingredients
        )))
        for i in ins.all():
            file_content += f'{i.name} {i.amount_sum} {i.measurement_unit}'
        return Response('Запись в списке покупок удалена', status=status.HTTP_204_NO_CONTENT)   

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if Shopping_cart.objects.filter(recipe=recipe, owner=request.user).exists():
                raise ValidationError(detail={'Список покупок': 'Запись уже существует.'})
        
            Shopping_cart.objects.create(owner=request.user,
                                     recipe=recipe)
            serializer = Shopping_cartRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            get_object_or_404(Shopping_cart, recipe=recipe, owner=request.user).delete()
            return Response('Запись в списке покупок удалена', status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe.objects.all(), id=pk)
        if request.method == 'POST':
            if Favorites.objects.filter(recipe=recipe).exists():
                raise ValidationError(detail={'Избранное': 'Запись уже существует.'})
        
            Favorites.objects.create(user=request.user,
                                     recipe=recipe)
            serializer = FavoritesRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            get_object_or_404(Favorites.objects.all(), recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_context(self):
        context = super(RecipeViewSet, self).get_serializer_context()
        context.update({"request": self.request})
        return context

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = self.perform_update(serializer)
        response_data = ResponseRecipeSerializer(recipe,
            context=self.get_serializer_context()).data
        for ingredient in response_data['ingredients']:
            recipe_ingredient = get_object_or_404(Ingredient.objects.all(),
                                                  id=ingredient['id'])
            ingredient['amount'] = get_object_or_404(RecipesIngredients.objects.all(),
                                                     recipe=recipe,
                                                     ingredient=recipe_ingredient).amount
        return Response(response_data)

    def perform_update(self, serializer):
        return serializer.save()

    def retrieve(self, request, *args, **kwargs):
        recipe = self.get_object()
        response_data = ResponseRecipeSerializer(recipe,
            context=self.get_serializer_context()).data
        for ingredient in response_data['ingredients']:
            recipe_ingredient = get_object_or_404(Ingredient.objects.all(),
                                                  id=ingredient['id'])
            ingredient['amount'] = get_object_or_404(RecipesIngredients.objects.all(),
                                                     recipe=recipe,
                                                     ingredient=recipe_ingredient).amount
        return Response(response_data)

    def list(self, request, *args, **kwargs):
        queryset = Recipe.objects.all()
        response_data = ResponseRecipeSerializer(queryset,
            many=True, context=self.get_serializer_context()).data
        for recipe in response_data:
            for ingredient in recipe['ingredients']:
                recipe_ingredient = get_object_or_404(Ingredient.objects.all(),
                                                  id=ingredient['id'])
                recipe_object = get_object_or_404(queryset,
                                                  id=recipe['id'])
                ingredient['amount'] = get_object_or_404(RecipesIngredients.objects.all(),
                                                     recipe=recipe_object,
                                                     ingredient=recipe_ingredient).amount
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(response_data)

        return Response(response_data)

    def create(self, request, *args, **kwargs):
        serializer = RecipeSerializer(data=request.data,
            context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        recipe = self.perform_create(serializer)
        response_serializer = ResponseRecipeSerializer(recipe,
            context=self.get_serializer_context())
        response_data = response_serializer.data
        for ingredient in response_data['ingredients']:
            recipe_ingredient = get_object_or_404(Ingredient.objects.all(),
                                                  id=ingredient['id'])
            ingredient['amount'] = get_object_or_404(RecipesIngredients.objects.all(),
                                                     recipe=recipe,
                                                     ingredient=recipe_ingredient).amount
        return Response(response_data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        return serializer.save()


def error404(request, exception):
    response_data = {}
    response_data['detail'] = 'Not found.'
    return HttpResponseNotFound(json.dumps(response_data), content_type="application/json")
