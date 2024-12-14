"""Модуль для хранения констант."""

# Ограничения длины полей
NAME_LENGTH = 32
SLUG_LENGTH = 32
INGREDIENT_NAME_LENGTH = 128
MEASUREMENT_UNIT_LENGTH = 64
RECIPE_NAME_LENGTH = 256

# Ограничения значений
MIN_AMOUNT = 1
MAX_AMOUNT = 32000
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 32000

# Ограничения для аватара
MAX_AVATAR_SIZE_MB = 2
MAX_AVATAR_SIZE_BYTES = MAX_AVATAR_SIZE_MB * 1024 * 1024

# Сообщения об ошибках для рецептов
RECIPE_NAME_REQUIRED = 'Название рецепта обязательно.'
RECIPE_NAME_EMPTY = 'Название рецепта не может быть пустым.'
RECIPE_TEXT_REQUIRED = 'Описание рецепта обязательно.'
RECIPE_TEXT_EMPTY = 'Описание рецепта не может быть пустым.'
COOKING_TIME_ERROR = (
    f'Время приготовления должно быть от {MIN_COOKING_TIME} '
    f'до {MAX_COOKING_TIME} минут.'
)

# Сообщения об ошибках для ингредиентов
INGREDIENT_AMOUNT_MIN_ERROR = f'Количество должно быть больше {MIN_AMOUNT}'
INGREDIENT_AMOUNT_MAX_ERROR = f'Количество должно меньше {MAX_AMOUNT}'
INGREDIENTS_REQUIRED_ERROR = 'Это поле обязательно.'
INVALID_INGREDIENTS_ERROR = 'Некорректные данные. Ожидался список.'
NO_INGREDIENTS_ERROR = 'Необходимо указать хотя бы один ингредиент.'
DUPLICATE_INGREDIENTS_ERROR = 'Ингредиент указан более одного раза.'
INGREDIENT_NOT_EXIST_ERROR = 'Ингредиент не существует.'

# Сообщения об ошибках для тегов
TAG_NOT_EXISTS = 'Тег с идентификатором {pk_value} не существует'
TAG_INCORRECT_TYPE = 'Некорректный тип данных. Ожидался ID тега'
NO_TAGS_ERROR = 'Необходимо указать хотя бы один тег.'
DUPLICATE_TAGS_ERROR = 'Теги не должны повторяться.'

# Сообщения для избранного и корзины покупок
ERROR_RECIPE_ALREADY_FAVORITED = 'Рецепт уже добавлен в избранное'
RECIPE_ALREADY_IN_CART = 'Рецепт уже в списке покупок'

# Сообщения для аватара
AVATAR_ERROR = 'Размер изображения не должен превышать'
AVATAR_SIZE_EXCEEDED = f'{AVATAR_ERROR} {MAX_AVATAR_SIZE_MB}MB'

# Ошибки подписок

ERROR_SELF_SUBSCRIBE = 'Нельзя подписаться на самого себя'
ERROR_ALREADY_SUBSCRIBED = 'Вы уже подписаны на этого автора'

# Общие сообщения
EMPTY = '---'
