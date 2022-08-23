from tkinter import CASCADE
from unicodedata import name

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()

class Ingredient(models.Model):
    name = models.CharField(
        'Ингредиент',
        max_length=200,
        help_text='Название ингредиента')
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=200,
        help_text='Единица измерения (например: кг, л, мл)'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        'Тег',
        max_length=200,
        help_text='Название тега')
    color = models.CharField(
        'Цвет',
        max_length=7,
        help_text='Название цвета')
    slug = models.SlugField(
        'Слаг',
        max_length=200,
        unique=True,
        help_text='Название слага')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.slug


class Recipe(models.Model):
    ingredients = models.ManyToManyField(
              Ingredient,
              through='RecipesIngredients',
              through_fields=('recipe', 'ingredient'))
    tags = models.ManyToManyField(
       Tag)
    name = models.CharField(
        'Название рецепта',
        max_length=200,
        help_text='Название рецепта'
    )
    text = models.TextField(
        'Текст рецепта',
        help_text='Текст рецепта'
    )
    cooking_time = models.IntegerField(
        'Время приготовления',
        help_text='Время приготовления',
        validators=[MinValueValidator(1),]
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/images/'
    )
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE
        )


    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipesIngredients(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE)
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    amount = models.IntegerField(
        'Количество ингридиента',
        help_text='Количество ингридиента'
    )


class Favorites(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Рецепты в избранном'
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'
            ),
        )


class Shopping_cart(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = (
            models.UniqueConstraint(
                fields=['owner', 'recipe'],
                name='unique_owner_recipe'
            ),
        )
