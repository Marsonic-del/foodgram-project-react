import csv

from recipes.models import Ingredient


def run():
    with open('C:/Users/User/Pdev/foodgram-project-react/backend/foodgram/scripts/ingredients.csv', encoding="utf8") as file:
        reader = csv.reader(file, dialect=csv.excel)
        next(reader)  # Advance past the header

        Ingredient.objects.all().delete()

        for row in reader:
            print(row)
            ingredient = Ingredient(
                name=row[0],
                measurement_unit=row[-1])
            ingredient.save()
