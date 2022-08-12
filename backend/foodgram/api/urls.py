from django.conf.urls import include
from django.urls import path

from .routers import CustomRouter
from .views import UserViewSet, delete_token, get_token, set_password

custom_router = CustomRouter()
custom_router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('users/set_password/', set_password, name='set_password'),
    path('', include(custom_router.urls)),
    path('auth/token/login/', get_token, name='get_token'),
    path('auth/token/logout/', delete_token, name='delete_token'),
]
