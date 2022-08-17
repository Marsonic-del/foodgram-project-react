import imp
from email import message

from api.permissions import RecipePermissions
from django import http
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from .models import Favorites, Ingredient, Recipe, RecipesIngredients, Tag
from .serializers import (FavoritesRecipeSerializer, IngredientSerializer,
                          RecipeSerializer, ResponseRecipeSerializer,
                          TagSerializer)

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

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if Favorites.objects.filter(recipe=recipe).exists():
                raise ValidationError(detail={'Избранное': 'Такая запись уже существует.'})
        
            Favorites.objects.create(user=request.user,
                                     recipe=recipe)
            serializer = FavoritesRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            get_object_or_404(Favorites, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = self.perform_update(serializer)
        response_data = ResponseRecipeSerializer(recipe).data
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
        response_data = ResponseRecipeSerializer(recipe).data
        for ingredient in response_data['ingredients']:
            recipe_ingredient = get_object_or_404(Ingredient.objects.all(),
                                                  id=ingredient['id'])
            ingredient['amount'] = get_object_or_404(RecipesIngredients.objects.all(),
                                                     recipe=recipe,
                                                     ingredient=recipe_ingredient).amount
        return Response(response_data)

    def list(self, request, *args, **kwargs):
        queryset = Recipe.objects.all()
        response_data = ResponseRecipeSerializer(queryset,many=True).data
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = self.perform_create(serializer)
        response_data = ResponseRecipeSerializer(recipe).data
        for ingredient in response_data['ingredients']:
            recipe_ingredient = get_object_or_404(Ingredient.objects.all(),
                                                  id=ingredient['id'])
            ingredient['amount'] = get_object_or_404(RecipesIngredients.objects.all(),
                                                     recipe=recipe,
                                                     ingredient=recipe_ingredient).amount
        return Response(response_data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        return serializer.save()


class CreateDestroyAPIView(mixins.DestroyModelMixin,
                        mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    pass


'''class FavoritesViewSet(CreateDestroyAPIView):
    queryset = Favorites.objects.all()
    serializer_class = FavoritesRecipeSerializer

    def create(self, request, *args, **kwargs):
        recipe_id = request.parser_context['view'].kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if Favorites.objects.filter(recipe=recipe).exists():
            raise ValidationError(detail={'Избранное': 'Такая запись уже существует.'})
        
        fav = Favorites.objects.create(user=request.user,
                                 recipe=recipe)
        print(fav)
        serializer = FavoritesRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        Favorites.objects.delete(
            recipe=Recipe.objects.get(id=request.parser_context['view'].kwargs['pk']))
        return Response(status=status.HTTP_204_NO_CONTENT)'''
