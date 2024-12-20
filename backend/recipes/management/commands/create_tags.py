from django.core.management.base import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    help = 'Create basic tags'

    def handle(self, *args, **options):
        tags_data = [
            {'name': 'Завтрак', 'slug': 'breakfast'},
            {'name': 'Обед', 'slug': 'lunch'},
            {'name': 'Ужин', 'slug': 'dinner'},
        ]

        tags_created = 0
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(**tag_data)
            if created:
                tags_created += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {tags_created} tags')
        )
