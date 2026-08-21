"""Пагинация с параметром limit."""
from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """Пагинатор DRF с размером страницы из query-параметра limit."""

    page_size_query_param = 'limit'
    max_page_size = 100
