from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import OuterRef, Prefetch, Subquery
from recipes.models import Recipe
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from users.models import Subscription

from .permissions import UserPermissions
from .serializers import (ChangePasswordSerializer,
                          SubscribtionRecipeSerializer,
                          SubscribtionUserSerializer, TokenSerializer,
                          UserSerializer)

User = get_user_model()


class CreateListRetrieveViewSet(mixins.CreateModelMixin,
                                mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    pass


class UserViewSet(CreateListRetrieveViewSet):
    queryset = User.objects.get_queryset().order_by('id')
    serializer_class = UserSerializer
    permission_classes = (UserPermissions,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        serialized_data = serializer.data
        # Удаляем из ответа is_subscribed
        serialized_data.pop('is_subscribed', None)
        headers = self.get_success_headers(serializer.data)
        return Response(serialized_data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object(request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_object(self, request):
        if request.parser_context['kwargs']['pk'] == 'me':
            user_id = request.user.id
            obj = get_object_or_404(User.objects.all(), id=user_id)
            return obj
        return super().get_object()

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        my_subscriptions = Subscription.objects.prefetch_related(
            'author', 'subscriber').filter(subscriber=request.user)
        sq = Subquery(Recipe.objects.filter(
            author=OuterRef('pk')).order_by('id')[:2])
        p = Prefetch('recipes', queryset=Recipe.objects.filter(
            id__in=Subquery(Recipe.objects.filter(
                author=OuterRef('author')).values_list('id', flat=True)[:1])))
        authors = User.objects.filter(subscription_authors__subscriber=request.user).prefetch_related(p)
        serializer = SubscribtionUserSerializer(authors, many=True)
        #print(authors)
        #recipes = Recipe.objects.filter(author=author)[:recipes_limit]
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        recipes_limit = int(request.query_params['recipes_limit'][0])
        try:
            author = User.objects.get(id=pk)
        except ObjectDoesNotExist:
            raise NotFound(detail={'Подписки': 'Автор не существует.'}, code=404)
        if author == request.user:
            raise ValidationError(detail={'Подписки': 'Подписка на самого себя запрещена.'})
        if request.method == 'POST':
            if Subscription.objects.filter(author=author, subscriber=request.user).exists():
                raise ValidationError(detail={'Подписки': 'Подписка уже существует.'})
            Subscription.objects.create(subscriber=request.user, author=author)
            recipes = Recipe.objects.filter(author=author)[:recipes_limit]
            response_data = SubscribtionUserSerializer(author).data
            response_data['recipes'] = SubscribtionRecipeSerializer(recipes, many=True).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            try:
                Subscription.objects.select_related('author', 'subscriber').get(
                    author=author, subscriber=request.user).delete()
            except ObjectDoesNotExist:
                raise NotFound(detail={'Подписки': 'Подписка не существует.'})
            return Response('Подписка удалена.', status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def get_token(request):
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data.get('email')
    password = serializer.validated_data.get('password')
    user = get_object_or_404(User.objects.all(), email=email)
    if not check_password(password, user.password):
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
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

