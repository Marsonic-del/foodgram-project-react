import base64
from email.mime import image
from urllib import request

from api.serializers import UserSerializer
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from drf_extra_fields.fields import Base64ImageField
from foodgram.settings import HOST_NAME, MEDIA_ROOT
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from .models import Ingredient, Recipe, RecipesIngredients, Tag


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


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientsInRercipeSerializer(many=True)
    #image = serializers.CharField()
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

