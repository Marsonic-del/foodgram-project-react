from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorites, Ingredient, Recipe, RecipesIngredients,
                            Shopping_cart, Tag)
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from users.models import Subscription

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = ('email', 'username', 'first_name',
                  'last_name', 'id', 'password', 'is_subscribed')
        model = User
        extra_kwargs = {'password': {'write_only': True}}

    def get_is_subscribed(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return Subscription.objects.filter(
            author=obj, subscriber=self.context['request'].user).exists()


class CustomCreateUserSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name',
                  'last_name', 'id', 'password')


class SubscribtionRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class RecipesIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id')
    name = serializers.StringRelatedField(source='ingredient.name')
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit'
        )

    class Meta:
        fields = ('amount', 'id', 'name', 'measurement_unit')
        model = RecipesIngredients


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    ingredients = RecipesIngredientsSerializer(
        source='recipesingredients_set', many=True, read_only=True
        )
    tags = TagSerializer(
        read_only=True,
        many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = ('id', 'name', 'image', 'ingredients',
                  'tags', 'text', 'cooking_time', 'author',
                  'is_favorited', 'is_in_shopping_cart')
        model = Recipe

    def get_is_favorited(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return Favorites.objects.filter(
            user=self.context['request'].user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return Shopping_cart.objects.filter(
            user=self.context['request'].user, recipe=obj).exists()

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Список ингредиентов не может быть пустым'
            )
        ingredient_list = []
        for ingredient_item in ingredients:
            ingredient_id = ingredient_item.get('id')
            ingredient = get_object_or_404(Ingredient,
                                           id=ingredient_id)
            if ingredient in ingredient_list:
                raise serializers.ValidationError('Ингредиенты должны '
                                                  'быть уникальными')
            ingredient_list.append(ingredient)
            amount = ingredient_item.get('amount')
            if int(amount) <= 0:
                raise serializers.ValidationError('Проверьте, что количество'
                                                  'ингредиента больше нуля')

        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Нужно выбрать хотя бы один тэг!'
            })
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise serializers.ValidationError({
                    'tags': 'Тэги должны быть уникальными!'
                })
            tags_list.append(tag)

        cooking_time = data.get('cooking_time')
        if int(cooking_time) <= 0:
            raise serializers.ValidationError({
                'cooking_time': 'Время приготовление должно быть больше нуля!'
            })
        data['ingredients'] = ingredients
        data['tags'] = tags
        return data

    def create_ingredients_amount(self, recipe, ingredients):
        RecipesIngredients.objects.bulk_create(
            [RecipesIngredients(
                ingredient=get_object_or_404(
                            Ingredient.objects.all(), id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    def create(self, validated_data):
        pop_ingredients = validated_data.pop('ingredients')
        pop_tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=self.context['request'].user,
                                       **validated_data)
        recipe.tags.set(pop_tags)
        self.create_ingredients_amount(recipe, pop_ingredients)
        return recipe

    def update(self, recipe, validated_data):
        pop_ingredients = validated_data.pop('ingredients')
        pop_tags = validated_data.pop('tags')
        super().update(recipe, validated_data)
        recipe.ingredients.clear()
        recipe.tags.clear()
        self.create_ingredients_amount(recipe, pop_ingredients)
        recipe.tags.set(pop_tags)
        recipe.save()
        return recipe


class SubscribtionUserSerializer(serializers.ModelSerializer):
    recipes = SubscribtionRecipeSerializer(many=True)
    is_subscribed = serializers.BooleanField(default=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes_count', 'recipes')

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FavoritesRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class Shopping_cartRecipeSerializer(FavoritesRecipeSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
