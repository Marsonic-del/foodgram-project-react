from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from .views import (CustomUserViewSet, IngredientViewSet, RecipeViewSet,
                    TagViewSet)

router = SimpleRouter()
user_router = DefaultRouter()
user_router.register('users', CustomUserViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(user_router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
