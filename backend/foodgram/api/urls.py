from django.conf.urls import include
from django.urls import path
from recipes.views import IngredientViewSet, RecipeViewSet, TagViewSet
from rest_framework.routers import SimpleRouter

from .views import UserViewSet, delete_token, get_token, set_password

router = SimpleRouter()
router.register('users', UserViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('users/set_password/', set_password, name='set_password'),
    path('', include(router.urls)),
    path('auth/token/login/', get_token, name='get_token'),
    path('auth/token/logout/', delete_token, name='delete_token'),
]
