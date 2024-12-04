from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Административная панель для управления пользователями.
    """

    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_staff',
        'date_joined',
        'get_recipes_count',
        'get_subscribers_count',
    )
    list_display_links = ('id', 'username', 'email')
    list_filter = (
        'is_active',
        'is_staff',
        'date_joined',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
    )
    ordering = ('-date_joined',)

    fieldsets = (
        (
            'Основная информация',
            {
                'fields': (
                    'username',
                    'email',
                    'password',
                )
            },
        ),
        (
            'Персональные данные',
            {
                'fields': (
                    'first_name',
                    'last_name',
                )
            },
        ),
        (
            'Права доступа',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
                'classes': ('collapse',),
            },
        ),
        (
            'Важные даты',
            {
                'fields': (
                    'last_login',
                    'date_joined',
                ),
                'classes': ('collapse',),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'username',
                    'email',
                    'password1',
                    'password2',
                    'first_name',
                    'last_name',
                ),
            },
        ),
    )

    readonly_fields = ('date_joined', 'last_login')
    filter_horizontal = ('groups', 'user_permissions')

    def get_recipes_count(self, obj):
        """
        Возвращает количество рецептов, созданных пользователем.
        """
        return obj.recipe.count()

    get_recipes_count.short_description = 'Рецептов'

    def get_subscribers_count(self, obj):
        """
        Возвращает количество подписчиков пользователя.
        """
        return obj.follower.count()

    get_subscribers_count.short_description = 'Подписчиков'

    def get_inline_instances(self, request, obj=None):
        """
        Возвращает связанные модели для отображения в админке.
        """
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

