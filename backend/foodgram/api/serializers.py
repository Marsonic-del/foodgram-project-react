import base64
import re

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.files.base import ContentFile
from foodgram.settings import HOST_NAME
from recipes.models import Ingredient, Recipe, RecipesIngredients, Tag
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = ('email', 'username', 'first_name', 'last_name', 'id', 'password')
        model = User
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class TokenSerializer(serializers.Serializer):
    email = serializers.EmailField(allow_blank=False, label='Email address', max_length=254, required=True)
    password = serializers.CharField(allow_blank=False, label='password', max_length=150, required=True)


class ChangePasswordSerializer(serializers.ModelSerializer):
    """
    Serializer for password change endpoint.
    """
    current_password = serializers.CharField(max_length=150, required=True)
    new_password = serializers.CharField(max_length=150, required=True)

    class Meta:
        fields = ('current_password', 'new_password')
        model = User
        extra_kwargs = {'current_password': {'write_only': True},
                        'new_password': {'write_only': True}}

    def update(self, instance, validated_data):
        if not check_password(validated_data['current_password'], instance.password):
            raise ValidationError({'detail': 'current_password is incorrect'})
        instance.set_password(validated_data.get('new_password'))
        instance.save()
        return instance


class CustomImageField(serializers.Field):
    def to_representation(self, value):
        image_url = f'{HOST_NAME}media/{value.name}'
        return image_url

    def to_internal_value(self, data):
        try:
           format, imgstr = data.split(';base64,')
           ext = format.split('/')[-1]
           data = ContentFile(base64.b64decode(imgstr), name='image.' + ext)
        except ValueError:
            raise serializers.ValidationError('Некорректные данные картинки')
        return data


'''class SubscribtionRecipeSerializer(serializers.ModelSerializer):
    image = CustomImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribtionUserSerializer(serializers.ModelSerializer):
    #recipes = SubscribtionRecipeSerializer(many=True)
    is_subscribed = serializers.BooleanField(default=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed', 'recipes_count')

    def get_recipes_count(self, obj):
        return obj.recipes.count()'''


class SubscribtionRecipeSerializer(serializers.ModelSerializer):
    image = CustomImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribtionUserSerializer(serializers.ModelSerializer):
    recipes = SubscribtionRecipeSerializer(many=True)
    is_subscribed = serializers.BooleanField(default=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed', 'recipes_count', 'recipes')

    def get_recipes_count(self, obj):
        return obj.recipes.count()


'*********************************************************************'

class IngredientSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class TagSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class RecipesIngredientsSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = ('id', 'recipe', 'ingredient', 'amount')
        model = RecipesIngredients


class IngredientsInRercipeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()
    
    class Meta:
        fields = ('id', 'amount', )


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientsInRercipeSerializer(many=True)
    image = CustomImageField()
    author = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        fields = ('id', 'name', 'image', 'ingredients', 'tags', 'text', 'cooking_time', 'author')
        model = Recipe

    def update(self, recipe, validated_data):
        pop_ingredients = validated_data.pop('ingredients')
        pop_tags = validated_data.pop('tags')
        for attr, value in validated_data.items():
            setattr(recipe, attr, value)
        recipe.ingredients.clear()
        recipe.tags.clear()
        for ingredient in pop_ingredients:
            recipe_ingredient = get_object_or_404(Ingredient.objects.all(), id=ingredient['id'])
            RecipesIngredients.objects.create(
                recipe=recipe,
                ingredient=recipe_ingredient,
                amount=ingredient['amount'])
        for tag in pop_tags:
            recipe.tags.add(tag)
        recipe.save()
        return recipe

    def create(self, validated_data):
        pop_ingredients = validated_data.pop('ingredients')
        pop_tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=self.context['request'].user,
                                      **validated_data)
        for ingredient in pop_ingredients:
            recipe_ingredient = get_object_or_404(Ingredient.objects.all(), id=ingredient['id'])
            RecipesIngredients.objects.create(
                recipe=recipe,
                ingredient=recipe_ingredient,
                amount=ingredient['amount'])
        for tag in pop_tags:
            recipe.tags.add(tag)
        return recipe


class ResponseRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = IngredientSerializer(many=True)
    author = UserSerializer()
    image = CustomImageField()

    class Meta:
        fields = ('id', 'name', 'image', 'ingredients', 'tags', 'text', 'cooking_time', 'author')
        model = Recipe


class FavoritesRecipeSerializer(serializers.ModelSerializer):
    image = CustomImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
