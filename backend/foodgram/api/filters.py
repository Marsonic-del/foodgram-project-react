from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(filters.FilterSet):
    author = filters.NumberFilter(field_name='author__id')
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart')
    is_favorited = filters.BooleanFilter(method='get_is_favorited')
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
    )

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(
                shoppingcart__user=self.request.user
            )
        return queryset

    def get_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(
                favorite__user=self.request.user
            )
        return queryset

    class Meta:
        model = Recipe
        fields = ['author', 'is_in_shopping_cart', 'tags']


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name', lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ['name']
