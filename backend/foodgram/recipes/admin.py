from django.contrib import admin

from users.models import Subscription

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit', )
    search_fields = ('name',)
    list_filter = ('name', )
    empty_value_display = '-пусто-'


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount',
                    'measurement_unit_field')
    search_fields = ('recipe',)
    list_filter = ('recipe', )
    empty_value_display = '-пусто-'

    def measurement_unit_field(self, obj):
        return obj.ingredient.measurement_unit

    measurement_unit_field.short_description = 'Единица измерения'


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name',)
    list_filter = ('name', )
    empty_value_display = '-пусто-'


class RecipeIngredientInline(admin.StackedInline):
    model = RecipeIngredient
    fk_name = 'recipe'


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'get_Favorite')
    search_fields = ('name', 'author', 'tags')
    list_filter = ('author', 'tags', 'name')
    inlines = [RecipeIngredientInline]
    empty_value_display = '-пусто-'

    def get_Favorite(self, obj):
        return Favorite.objects.filter(recipe=obj).count()

    get_Favorite.short_description = 'Количество добавлений в избранное'


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user',)
    list_filter = ('user', )
    empty_value_display = '-пусто-'


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user',)
    list_filter = ('user', )
    empty_value_display = '-пусто-'


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'subscriber')
    search_fields = ('author', 'subscriber')
    list_filter = ('author', 'subscriber')
    empty_value_display = '-пусто-'


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
