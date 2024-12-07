from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = 'Creates 10 test users'

    def handle(self, *args, **kwargs):
        for i in range(1, 11):
            username = f'testuser{i}'
            email = f'testuser{i}@example.com'
            password = '12345'

            # Проверяем, существует ли пользователь
            if not User.objects.filter(email=email).exists():
                User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=f'Test{i}',
                    last_name=f'User{i}',
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created user: {email}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'User {email} already exists')
                )
