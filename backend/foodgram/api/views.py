from django.contrib.auth import get_user_model
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.permissions import CurrentUserOrAdmin
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .paginators import CustomPageNumberPagination
from .permissions import RecipePermissions, UserPermissions
from .serializers import (IngredientSerializer, SubscribtionUserSerializer,
                          TagSerializer, UserSerializer, WriteRecipeSerializer)
from .services import ViewsetForRecipes, get_pdf_file
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscription

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = (UserPermissions,)
    pagination_class = CustomPageNumberPagination

    @action(["get", ], permission_classes=(CurrentUserOrAdmin,), detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    @action(
        detail=False, methods=['get'],
        pagination_class=CustomPageNumberPagination,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        authors = User.objects.filter(
            subscription_authors__subscriber=request.user
        ).prefetch_related('subscribers'
                           ).prefetch_related('recipes').all()
        queryset = self.filter_queryset(authors)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = SubscribtionUserSerializer(
                page, many=True,
                context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = SubscribtionUserSerializer(
            authors.all(), many=True,
            context={'request': request})
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        try:
            author = User.objects.prefetch_related('recipes').get(id=id)
        except User.DoesNotExist:
            raise NotFound(
                detail={'????????????????': '?????????? ???? ????????????????????.'}, code=404)
        if author == request.user:
            return Response(
                '???????????????? ???? ???????????? ???????? ??????????????????.',
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            if Subscription.objects.filter(
                    author=author, subscriber=request.user
            ).exists():
                return Response(
                    '???????????????? ?????? ????????????????????.',
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(subscriber=request.user, author=author)
            response_data = SubscribtionUserSerializer(
                author, context={'request': request}).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            try:
                Subscription.objects.select_related(
                    'author', 'subscriber').get(
                    author=author, subscriber=request.user
                ).delete()
            except Subscription.DoesNotExist:
                raise NotFound(detail={'????????????????': '???????????????? ???? ????????????????????.'})
            return Response(
                '???????????????? ??????????????.', status=status.HTTP_204_NO_CONTENT
            )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None
    permission_classes = (AllowAny,)


class RecipeViewSet(ViewsetForRecipes):
    serializer_class = WriteRecipeSerializer
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
        ?????????????????? ?? ???????????????????? PDF ????????.

        ?? ?????????????????????????? ?? ???? ?????????????????????? ?? ???????????????? ?????????????????????? ???????????? ??????????????.
        """
        file_content = self.get_shopping_cart_content(request)
        return FileResponse(
            get_pdf_file(file_content),
            as_attachment=True,
            filename='ShoppingCart.pdf')

    @action(
        detail=True,
        methods=['post', 'delete']
    )
    def shopping_cart(self, request, pk=None):
        """?????????????????? ?? ?????????????? ???????????? ?? ???????????? ShoppingCart."""
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.add_recipe_to_user_shopping_cart(
                request, recipe=recipe
            )
        if request.method == 'DELETE':
            return self.remove_recipe_to_shopping_or_favorite(
                ShoppingCart, request, recipe=recipe)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        """?????????????????? ?? ?????????????? ???????????? ?? ???????????? Favorite."""
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.add_recipe_to_user_favorite(
                request, recipe=recipe
            )
        if request.method == 'DELETE':
            return self.remove_recipe_to_shopping_or_favorite(
                Favorite, request, recipe=recipe)
