from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from .routers import UserRouter
from .views import (CustomUserViewSet, IngredientViewSet, RecipeViewSet,
                    TagViewSet, delete_token, get_token, set_password)

router = SimpleRouter()
user_router = DefaultRouter()
user_router.register('users', CustomUserViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('users/set_password/', set_password, name='set_password'),
    path('', include(router.urls)),
    #path('auth/token/login/', get_token, name='get_token'),
    #path('auth/token/logout/', delete_token, name='delete_token'),
    path('', include(user_router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
