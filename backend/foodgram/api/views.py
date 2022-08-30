from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ObjectDoesNotExist
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.permissions import CurrentUserOrAdmin
from djoser.views import UserViewSet
from recipes.models import Favorites, Ingredient, Recipe, Shopping_cart, Tag
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from users.models import Subscription

from .filters import RecipeFilter
#from .mixins import CreateListRetrieveViewSet
from .paginators import CustomPageNumberPagination
from .permissions import RecipePermissions, UserPermissions
from .serializers import (ChangePasswordSerializer, IngredientSerializer,
                          RecipeSerializer, SubscribtionRecipeSerializer,
                          SubscribtionUserSerializer, TagSerializer,
                          TokenSerializer, UserSerializer)
from .services import ViewsetForRecipes, get_pdf_file

User = get_user_model()



class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    #permission_classes = (UserPermissions,)
    pagination_class = CustomPageNumberPagination

    @action(["get", ], permission_classes=(CurrentUserOrAdmin,), detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    '''def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        serialized_data = serializer.data
        # Удаляем из ответа is_subscribed
        serialized_data.pop('is_subscribed', None)
        headers = self.get_success_headers(serializer.data)
        return Response(serialized_data,
                        status=status.HTTP_201_CREATED, headers=headers)'''

    '''def retrieve(self, request, *args, **kwargs):
        instance = self.get_object(request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)'''

    '''def get_object(self, request):
        if request.parser_context['kwargs']['pk'] == 'me':
            user_id = request.user.id
            obj = get_object_or_404(User, id=user_id)
            return obj
        return super().get_object()'''

    @action(
            detail=False, methods=['get'],
            pagination_class=CustomPageNumberPagination,
            permission_classes=(permissions.IsAuthenticated,)
        )
    def subscriptions(self, request):
        recipes_limit = int(request.query_params['recipes_limit'])
        authors = User.objects.filter(
            subscription_authors__subscriber=request.user
            ).prefetch_related('recipes')
        queryset = self.filter_queryset(authors.all())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = SubscribtionUserSerializer(page, many=True)
            for author in serializer.data:
                author.update(
                    {'recipes': SubscribtionRecipeSerializer(
                                          authors.filter(
                                            id=author['id']
                                            ).get(
                                            ).recipes.all(
                                            )[:recipes_limit], many=True).data}
                                        )
            return self.get_paginated_response(serializer.data)

        serializer = SubscribtionUserSerializer(authors.all(), many=True)
        for author in serializer.data:
            author.update({'recipes': SubscribtionRecipeSerializer(
                    authors.filter(
                        id=author['id']).get(
                        ).recipes.all(
                        )[:recipes_limit], many=True).data})
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        try:
            author = User.objects.prefetch_related('recipes').get(id=pk)
        except ObjectDoesNotExist:
            raise NotFound(
                detail={'Подписки': 'Автор не существует.'}, code=404)
        if author == request.user:
            raise ValidationError(
                detail={'Подписки': 'Подписка на самого себя запрещена.'})
        if request.method == 'POST':
            recipes_limit = int(request.query_params.get('recipes_limit', 0))
            if Subscription.objects.filter(
                                    author=author, subscriber=request.user
                                    ).exists():
                raise ValidationError(
                    detail={'Подписки': 'Подписка уже существует.'})
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
            except ObjectDoesNotExist:
                raise NotFound(detail={'Подписки': 'Подписка не существует.'})
            return Response(
                'Подписка удалена.', status=status.HTTP_204_NO_CONTENT
                )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def get_token(request):
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data.get('email')
    password = serializer.validated_data.get('password')
    user = get_object_or_404(User.objects.all(), email=email)
    if not check_password(password, user.password):
        return Response(
            {'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND
            )
    token = str(AccessToken().for_user(user))
    return Response({'auth_token': token}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def delete_token(request):
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def set_password(request):
    user = get_object_or_404(User.objects.all(), id=request.user.id)
    serializer = ChangePasswordSerializer(user, data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


    # ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff

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
            return self.add_recipe_to_user_shopping_cart(
                request, recipe=recipe
                )
        if request.method == 'DELETE':
            return self.remove_recipe_to_shopping_or_favorite(
                Shopping_cart, request, recipe=recipe)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        """Добавляет и удаляет запись в модели Favorites."""
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.add_recipe_to_user_favorites(
                request, recipe=recipe
                )
        if request.method == 'DELETE':
            return self.remove_recipe_to_shopping_or_favorite(
                Favorites, request, recipe=recipe)
