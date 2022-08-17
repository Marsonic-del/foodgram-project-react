from django.conf.urls import include
from django.urls import path
from recipes.views import IngredientViewSet, RecipeViewSet, TagViewSet

from .routers import CustomRouter
from .views import UserViewSet, delete_token, get_token, set_password

custom_router = CustomRouter()
custom_router.register('users', UserViewSet, basename='users')
custom_router.register('ingredients', IngredientViewSet, basename='ingredients')
custom_router.register('tags', TagViewSet, basename='tags')
#custom_router.register(r"recipes/(?P<recipe_id>\d+)/favorite/?", FavoritesViewSet, basename='favorites')
custom_router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('users/set_password/', set_password, name='set_password'),
    path('', include(custom_router.urls)),
    path('auth/token/login/', get_token, name='get_token'),
    path('auth/token/logout/', delete_token, name='delete_token'),
]
