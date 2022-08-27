from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()


class UserAdmin(UserAdmin):
    list_display = (
        'username', 'email', 'first_name',
        'last_name', 'date_joined',
        'is_staff', 'password')
    fieldsets = ()
    search_fields = ('username', 'first_name', 'last_name',)
    list_filter = ('username', 'email',)
    empty_value_display = '-пусто-'


admin.site.register(User, UserAdmin)
