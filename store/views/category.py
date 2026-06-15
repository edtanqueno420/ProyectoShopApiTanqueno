# store/views/category.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count

from store.models               import Category
from store.serializers.category import CategorySerializer
from store.permissions          import IsStaffOrReadOnly
from store.filters              import CategoryFilter
from store.pagination           import StandardPagination


class CategoryViewSet(viewsets.ModelViewSet):
    queryset           = Category.objects.all()
    serializer_class   = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = CategoryFilter
    search_fields      = ['name', 'description']
    ordering_fields    = ['name', 'created_at']
    ordering           = ['name']

    # store/views/category.py — reemplazar la acción active_products
    @action(detail=True, methods=['get'], url_path='products')
    def active_products(self, request, pk=None):
        from store.models import Product
        from store.serializers.product import ProductSummarySerializer
        category = self.get_object()
        qs   = category.products.filter(is_active=True).order_by('name')
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(
                ProductSummarySerializer(page, many=True).data
            )
        return Response(ProductSummarySerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = Category.objects.annotate(num_products=Count('products', distinct=True))
        return Response({
            'total':    qs.count(),
            'active':   qs.filter(is_active=True).count(),
            'inactive': qs.filter(is_active=False).count(),
            'detail': [
                {
                    'id':           c.id,
                    'name':         c.name,
                    'num_products': c.num_products,
                    'is_active':    c.is_active,
                }
                for c in qs.order_by('name')
            ],
        })