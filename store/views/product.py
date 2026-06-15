# store/views/product.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Max, Min, Sum, Count

from store.models              import Product
from store.serializers.product import ProductSerializer, ProductSummarySerializer
from store.permissions         import IsStaffOrReadOnly
from store.filters             import ProductFilter
from store.pagination          import StandardPagination


class ProductViewSet(viewsets.ModelViewSet):
    queryset           = Product.objects.select_related('category').filter(is_active=True)
    serializer_class   = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = ProductFilter
    search_fields      = ['name', 'description', 'category__name']
    ordering_fields    = ['name', 'price', 'stock', 'created_at']
    ordering           = ['name']

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAdminUser],
        url_path='restock',
    )
    def restock(self, request, pk=None):
        product = self.get_object()
        try:
            quantity = int(request.data.get('quantity', 0))
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': 'Quantity must be a positive integer.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        product.stock += quantity
        product.save(update_fields=['stock'])
        return Response({
            'id':        product.id,
            'name':      product.name,
            'new_stock': product.stock,
        })

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='available',
    )
    def available(self, request):
        qs   = self.filter_queryset(
            self.get_queryset().filter(stock__gt=0, is_active=True)
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(
                ProductSummarySerializer(page, many=True).data
            )
        return Response(ProductSummarySerializer(qs, many=True).data)

    @action(
        detail=False,
        methods=['get'],
        url_path='stats',
    )
    def stats(self, request):
        qs      = Product.objects.all()
        active  = qs.filter(is_active=True)
        data    = active.aggregate(
            total_active  = Count('id'),
            avg_price     = Avg('price'),
            max_price     = Max('price'),
            min_price     = Min('price'),
            total_stock   = Sum('stock'),
        )
        data['total_inactive'] = qs.filter(is_active=False).count()
        data['out_of_stock']   = active.filter(stock=0).count()
        if data['avg_price']:
            data['avg_price'] = round(float(data['avg_price']), 2)
        return Response(data)