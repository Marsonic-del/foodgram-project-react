from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Ingredient, Tag


class IngredientSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class TagSerializer(serializers.ModelSerializer):
    
    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag
