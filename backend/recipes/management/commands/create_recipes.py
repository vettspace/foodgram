import os

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

from .test_recipes_data import TEST_RECIPES

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates test recipes'

    def handle(self, *args, **options):
        required_tags = ['breakfast', 'lunch', 'dinner']
        existing_tags = Tag.objects.filter(slug__in=required_tags)
        if len(existing_tags) != len(required_tags):
            self.stdout.write(
                self.style.ERROR('Not all required tags exist in database')
            )
            return

        for i in range(1, 11):
            username = f'testuser{i}'
            if not User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.ERROR(f'User {username} does not exist')
                )
                return

        # Путь к папке с тестовыми изображениями
        image_folder = 'recipes/management/commands/test_pics/'

        if not os.path.exists(image_folder):
            self.stdout.write(
                self.style.ERROR(f'Image folder {image_folder} does not exist')
            )
            return

        recipes_created = 0

        # Создание рецептов
        for i, recipe_data in enumerate(TEST_RECIPES, 1):
            try:
                username = f'testuser{i}'
                user = User.objects.get(username=username)

                ingredients_exist = all(
                    Ingredient.objects.filter(name=ing_name).exists()
                    for ing_name, _ in recipe_data['ingredients']
                )

                if not ingredients_exist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Ingredient for "{recipe_data["name"]}" not found'
                        )
                    )
                    continue

                image_path = os.path.join(image_folder, recipe_data['image'])
                if not os.path.exists(image_path):
                    self.stdout.write(
                        self.style.WARNING(
                            f'Image file {recipe_data["image"]} not found'
                        )
                    )
                    continue

                recipe = Recipe.objects.create(
                    author=user,
                    name=recipe_data['name'],
                    text=recipe_data['text'],
                    cooking_time=recipe_data['cooking_time'],
                )

                with open(image_path, 'rb') as img_file:
                    recipe.image.save(
                        recipe_data['image'], File(img_file), save=True
                    )

                for tag_slug in recipe_data['tags']:
                    tag = Tag.objects.get(slug=tag_slug)
                    recipe.tags.add(tag)

                # Добавляем ингредиенты
                for ing_name, amount in recipe_data['ingredients']:
                    try:
                        ingredient = Ingredient.objects.get(name=ing_name)
                        RecipeIngredient.objects.create(
                            recipe=recipe, ingredient=ingredient, amount=amount
                        )
                    except Ingredient.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                print('Ingredient not found in database')
                            )
                        )
                        continue

                recipes_created += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created recipe: {recipe_data["name"]}'
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error create recipe {recipe_data["name"]}: {str(e)}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {recipes_created} test recipes'
            )
        )
