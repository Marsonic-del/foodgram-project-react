from django.conf.urls import handler400, handler403, handler404, handler500
from django.contrib import admin
from django.urls import include, path
from recipes.views import error404

handler404 = error404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]
