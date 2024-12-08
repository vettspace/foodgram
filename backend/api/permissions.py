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

    def has_permission(self, request, view):
        return bool(
            request.method in permissions.SAFE_METHODS
            or request.user
            and request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user
            and (obj.author == request.user or request.user.is_staff)
        )
