from django.contrib.auth import get_user_model
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.permissions import CurrentUserOrAdmin
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscription

from .filters import RecipeFilter
from .paginators import CustomPageNumberPagination
from .permissions import RecipePermissions, UserPermissions
from .serializers import (IngredientSerializer, RecipeSerializer,
                          SubscribtionRecipeSerializer,
                          SubscribtionUserSerializer, TagSerializer,
                          UserSerializer)
from .services import (ViewsetForRecipes, get_pdf_file,
                       update_author_in_subscription)

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
        recipes_limit = int(request.query_params.get('recipes_limit', 0))
        authors = User.objects.filter(
            subscription_authors__subscriber=request.user
            ).prefetch_related('recipes')
        queryset = self.filter_queryset(authors.all())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = SubscribtionUserSerializer(page, many=True)
            update_author_in_subscription(serializer, authors, recipes_limit)
            return self.get_paginated_response(serializer.data)

        serializer = SubscribtionUserSerializer(authors.all(), many=True)
        update_author_in_subscription(serializer, authors, recipes_limit)
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
                detail={'Подписки': 'Автор не существует.'}, code=404)
        if author == request.user:
            return Response(
                'Подписка на самого себя запрещена.',
                status=status.HTTP_400_BAD_REQUEST
                )
        if request.method == 'POST':
            recipes_limit = int(request.query_params.get('recipes_limit', 0))
            if Subscription.objects.filter(
                                    author=author, subscriber=request.user
                                    ).exists():
                return Response(
                    'Подписка уже существует.',
                    status=status.HTTP_400_BAD_REQUEST
                    )
            Subscription.objects.create(subscriber=request.user, author=author)
            response_data = SubscribtionUserSerializer(author).data
            response_data['recipes'] = SubscribtionRecipeSerializer(
                                author.recipes.all()[:recipes_limit], many=True
                                ).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            try:
                Subscription.objects.select_related(
                    'author', 'subscriber').get(
                    author=author, subscriber=request.user
                    ).delete()
            except Subscription.DoesNotExist:
                raise NotFound(detail={'Подписки': 'Подписка не существует.'})
            return Response(
                'Подписка удалена.', status=status.HTTP_204_NO_CONTENT
                )


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
            filename='ShoppingCart.pdf')

    @action(
        detail=True,
        methods=['post', 'delete']
        )
    def shopping_cart(self, request, pk=None):
        """Добавляет и удаляет запись в модели ShoppingCart."""
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
        """Добавляет и удаляет запись в модели Favorite."""
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.add_recipe_to_user_favorite(
                request, recipe=recipe
                )
        if request.method == 'DELETE':
            return self.remove_recipe_to_shopping_or_favorite(
                Favorite, request, recipe=recipe)
