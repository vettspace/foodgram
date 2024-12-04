from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class PagePagination(PageNumberPagination):
    """
    Класс для пагинации.
    """

    page_size = settings.DEFAULT_PAGE_SIZE
    page_size_query_param = 'limit'
