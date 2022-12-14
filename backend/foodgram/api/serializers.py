from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id')
    name = serializers.StringRelatedField(source='ingredient.name')
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        fields = ('amount', 'id', 'name', 'measurement_unit')
        model = RecipeIngredient


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set', many=True, read_only=True
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
        return Favorite.objects.filter(
            user=self.context['request'].user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=self.context['request'].user, recipe=obj).exists()


class CreateRecipeIngredientSerializer(serializers.Serializer):
    amount = serializers.IntegerField()
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        fields = ('id', 'amount')
        model = Ingredient


class WriteRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    ingredients = CreateRecipeIngredientSerializer(many=True)

    class Meta:
        fields = ('id', 'name', 'image', 'ingredients',
                  'tags', 'text', 'cooking_time')
        model = Recipe

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                '???????????? ???????????????????????? ???? ?????????? ???????? ????????????'
            )
        ingredient_list = []
        for ingredient_item in ingredients:
            ingredient = ingredient_item.get('id')
            if ingredient in ingredient_list:
                raise serializers.ValidationError('?????????????????????? ???????????? '
                                                  '???????? ??????????????????????')
            ingredient_list.append(ingredient)
            amount = ingredient_item.get('amount')
            if int(amount) <= 0:
                raise serializers.ValidationError('??????????????????, ?????? ????????????????????'
                                                  '?????????????????????? ???????????? ????????')
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': '?????????? ?????????????? ???????? ???? ???????? ??????!'
            })
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise serializers.ValidationError({
                    'tags': '???????? ???????????? ???????? ??????????????????????!'
                })
            tags_list.append(tag)

        cooking_time = data.get('cooking_time')
        if int(cooking_time) <= 0:
            raise serializers.ValidationError({
                'cooking_time': '?????????? ?????????????????????????? ???????????? ???????? ???????????? ????????!'
            })
        return data

    def create_ingredients_amount(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                ingredient=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount']
            )for ingredient in ingredients])

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
        return recipe

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class SubscribtionUserSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(default=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes_count', 'recipes')

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get(
            'recipes_limit', obj.recipes.count())
        recipes = Recipe.objects.filter(
            author=obj).all()[:(int(recipes_limit))]
        context = {'request': request}
        return SubscribtionRecipeSerializer(
            recipes, many=True, context=context).data


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartRecipeSerializer(FavoriteRecipeSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
