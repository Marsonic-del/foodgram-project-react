from django.contrib import admin
from users.models import Subscription

from .models import (Favorites, Ingredient, Recipe, RecipesIngredients,
                     Shopping_cart, Tag)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit', )
    search_fields = ('name',)
    list_filter = ('name', )
    empty_value_display = '-пусто-'


class RecipesIngredientsAdmin(admin.ModelAdmin):
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


class RecipesIngredientsInline(admin.StackedInline):
    model = RecipesIngredients
    fk_name = 'recipe'


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'get_favorites')
    search_fields = ('name', 'author', 'tags')
    list_filter = ('author', 'tags', 'name')
    inlines = [RecipesIngredientsInline]
    empty_value_display = '-пусто-'

    def get_favorites(self, obj):
        return Favorites.objects.filter(recipe=obj).count()

    get_favorites.short_description = 'Количество добавлений в избранное'


class FavoritesAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user',)
    list_filter = ('user', )
    empty_value_display = '-пусто-'


class Shopping_cartAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'recipe')
    search_fields = ('owner',)
    list_filter = ('owner', )
    empty_value_display = '-пусто-'


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'subscriber')
    search_fields = ('author', 'subscriber')
    list_filter = ('author', 'subscriber')
    empty_value_display = '-пусто-'


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorites, FavoritesAdmin)
admin.site.register(Shopping_cart, Shopping_cartAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(RecipesIngredients, RecipesIngredientsAdmin)
