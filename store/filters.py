# store/filters.py
import django_filters
from store.models import Category, Product, Order


class CategoryFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model  = Category
        fields = ['is_active']


class ProductFilter(django_filters.FilterSet):
    name          = django_filters.CharFilter(lookup_expr='icontains')
    price_min     = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max     = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    stock_min     = django_filters.NumberFilter(field_name='stock', lookup_expr='gte')
    stock_max     = django_filters.NumberFilter(field_name='stock', lookup_expr='lte')
    category_name = django_filters.CharFilter(
        field_name='category__name', lookup_expr='icontains'
    )

    class Meta:
        model  = Product
        fields = ['is_active', 'category']


class OrderFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    to_date   = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model  = Order
        fields = ['status']