# Generated by Django 4.1 on 2022-08-15 09:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='name',
            field=models.CharField(help_text='Название ингредиента', max_length=200, unique=True, verbose_name='Ингредиент'),
        ),
    ]
