import base64
from email.mime import image
from urllib import request

from api.serializers import UserSerializer
from django.core.files.base import ContentFile
from drf_extra_fields.fields import Base64ImageField
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


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientsInRercipeSerializer(many=True)
    #tags = TagSerializer(many=True, read_only=True)
    image = serializers.CharField()
    author = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault())
    class Meta:
        fields = ('id', 'name', 'image', 'ingredients', 'tags', 'text', 'cooking_time', 'author')
        model = Recipe

    def create(self, validated_data):
        pop_ingredients = validated_data.pop('ingredients')
        pop_tags = validated_data.pop('tags')
        pop_image = validated_data.pop('image')
        '''image_data = validated_data.pop('image')
        print(image_data)
        format, imgstr = image_data.split(';base64,')
        name, ext = format.split('/')

        data = ContentFile(base64.b64decode(imgstr))  
        file_name = f'{name}.{ext}'''
        format, imgstr = pop_image.split(';base64,')
        ext = format.split('/')[-1]
        data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        recipe = Recipe.objects.create(author=self.context['request'].user,
                                       image=data,
                                       **validated_data,
                                      )
        #recipe.image.save(file_name, data, save=True)
        for ingredient in pop_ingredients:
            recipe_ingredient = get_object_or_404(Ingredient.objects.all(), id=ingredient['id'])
            RecipesIngredients.objects.create(
                recipe=recipe,
                ingredient=recipe_ingredient,
                amount=ingredient['amount'])
        for tag in pop_tags:
            recipe.tags.add(tag)
        print(self.data)
        return recipe

