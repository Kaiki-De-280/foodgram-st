from rest_framework.pagination import PageNumberPagination


class UserSubscrRecipePagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 10
