import imp
from email import message

from django import http
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework_simplejwt.tokens import AccessToken

from .models import Ingredient, Recipe, RecipesIngredients, Tag
from .serializers import (IngredientSerializer, RecipeSerializer,
                          ResponseRecipeSerializer, TagSerializer)

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
    pagination_class = None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = self.perform_create(serializer)
        response_data = ResponseRecipeSerializer(recipe).data
        print(request.build_absolute_uri(response_data['image']))
        abs_image_url = request.build_absolute_uri(response_data['image'])
        #response_data['image'] = abs_image_url
        for ingredient in response_data['ingredients']:
            recipe_ingredient = get_object_or_404(Ingredient.objects.all(),
                                                  id=ingredient['id'])
            ingredient['amount'] = get_object_or_404(RecipesIngredients.objects.all(),
                                                     recipe=recipe,
                                                     ingredient=recipe_ingredient).amount
        return Response(response_data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        return serializer.save()

