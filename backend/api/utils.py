import csv

from django.http import HttpResponse


def generate_shopping_cart_csv(shopping_cart):
    """Генерация CSV файла со списком покупок."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="shopping_list.csv"'
    )

    writer = csv.writer(response)
    # Записываем заголовок
    writer.writerow(['Ингредиент', 'Количество', 'Единица измерения'])

    if shopping_cart:
        # Записываем данные
        for item in shopping_cart:
            writer.writerow(
                [
                    item['ingredients__name'],
                    item['amount'],
                    item['ingredients__measurement_unit'],
                ]
            )
    else:
        writer.writerow(['Список покупок пуст'])

    return response