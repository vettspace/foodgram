from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение, позволяющее доступ только администраторам
    для небезопасных методов.
    """

    def has_permission(self, request, view):
        """
        Проверяет, имеет ли пользователь разрешение на выполнение запроса.
        """
        return (
            request.method in permissions.SAFE_METHODS or request.user.is_staff
        )


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение, позволяющее доступ автору объекта или администратору.
    """

    def has_object_permission(self, request, view, obj):
        """
        Проверяет, имеет ли пользователь разрешение
        на выполнение запроса для конкретного объекта.
        """
        return (
            obj.author == request.user
            or request.method in permissions.SAFE_METHODS
            or request.user.is_superuser
        )
