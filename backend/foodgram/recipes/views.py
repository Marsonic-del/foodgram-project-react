import json

from api.filters import RecipeFilter
from api.paginators import CustomPageNumberPagination
from api.permissions import RecipePermissions
from api.serializers import (IngredientSerializer, RecipeSerializer,
                             ResponseRecipeSerializer, TagSerializer)
from api.services import ViewsetForRecipes, get_pdf_file
from django.contrib.auth import get_user_model
from django.http import FileResponse, HttpResponseNotFound
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (Favorites, Ingredient, Recipe, RecipesIngredients,
                     Shopping_cart, Tag)

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None
    permission_classes = (AllowAny,)


class RecipeViewSet(ViewsetForRecipes):
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    permission_classes = (RecipePermissions,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPageNumberPagination

    @action(
        detail=False,
        methods=['get', ],
        permission_classes=[IsAuthenticated]
        )
    def download_shopping_cart(self, request, pk=None):
        """
        Формирует и отправляет PDF файл.

        С ингридиентами и их количеством в рецептах добавленных список покупок.
        """
        file_content = self.get_shopping_cart_content(request)
        return FileResponse(
            get_pdf_file(file_content),
            as_attachment=True,
            filename='shopping_cart.pdf')

    @action(
        detail=True,
        methods=['post', 'delete']
        )
    def shopping_cart(self, request, pk=None):
        """Добавляет и удаляет запись в модели Shopping_cart."""
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = self.add_recipe_to_user_shopping_cart(
                request, recipe=recipe
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            get_object_or_404(
                Shopping_cart, recipe=recipe, owner=request.user
                ).delete()
            return Response(
                'Запись в списке покупок удалена',
                status=status.HTTP_204_NO_CONTENT
                )

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        """Добавляет и удаляет запись в модели Favorites."""
        recipe = get_object_or_404(Recipe.objects.all(), id=pk)
        if request.method == 'POST':
            serializer = self.add_recipe_to_user_favorites(
                request, recipe=recipe
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            get_object_or_404(Favorites.objects.all(), recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    '''def get_serializer_context(self):
        """Переопределяем метод get_serializer_context."""
        context = super(RecipeViewSet, self).get_serializer_context()
        context.update({"request": self.request})
        return context'''

    '''def update(self, request, *args, **kwargs):
        """Переопределяем метод update."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = self.perform_update(serializer)
        response_data = ResponseRecipeSerializer(
            recipe,
            context=self.get_serializer_context()
            ).data
        for ingredient in response_data['ingredients']:
            recipe_ingredient = get_object_or_404(Ingredient.objects.all(),
                                                  id=ingredient['id'])
            ingredient['amount'] = get_object_or_404(
                RecipesIngredients.objects.all(),
                recipe=recipe,
                ingredient=recipe_ingredient).amount
        return Response(response_data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        """Переопределяем метод perform_update."""
        return serializer.save()

    def retrieve(self, request, *args, **kwargs):
        """Переопределяем метод retrieve."""
        recipe = self.get_object()
        response_data = ResponseRecipeSerializer(
            recipe,
            context=self.get_serializer_context()
            ).data
        for ingredient in response_data['ingredients']:
            recipe_ingredient = get_object_or_404(
                Ingredient.objects.all(),
                id=ingredient['id']
                )
            ingredient['amount'] = get_object_or_404(
                RecipesIngredients.objects.all(),
                recipe=recipe,
                ingredient=recipe_ingredient
                ).amount
        return Response(response_data)

    def list(self, request, *args, **kwargs):
        """Переопределяем метод list."""
        if request.user.is_anonymous:
            queryset = self.get_queryset()
        else:
            queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        serializer = ResponseRecipeSerializer(
            page,
            many=True,
            context=self.get_serializer_context()
            )
        if page is not None:
            return self.get_paginated_response(serializer.data)

        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Переопределяем метод create."""
        serializer = RecipeSerializer(
            data=request.data,
            context=self.get_serializer_context()
            )
        serializer.is_valid(raise_exception=True)
        recipe = self.perform_create(serializer)
        response_serializer = ResponseRecipeSerializer(
            recipe,
            context=self.get_serializer_context()
            )
        response_data = response_serializer.data
        for ingredient in response_data['ingredients']:
            recipe_ingredient = get_object_or_404(
                Ingredient.objects.all(),
                id=ingredient['id'])
            ingredient['amount'] = get_object_or_404(
                RecipesIngredients.objects.all(),
                recipe=recipe,
                ingredient=recipe_ingredient
                ).amount
        return Response(response_data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        """Переопределяем метод perform_create.

        Чтобы возвратить instance
        """
        return serializer.save()'''


def error404(request, exception):
    """Страница 404."""
    response_data = {}
    response_data['detail'] = 'Not found.'
    return HttpResponseNotFound(
        json.dumps(response_data), content_type="application/json"
        )
