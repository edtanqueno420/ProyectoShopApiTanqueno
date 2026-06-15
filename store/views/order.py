# store/views/order.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from store.models import Order, OrderItem, Product
from store.serializers.order import OrderSerializer, AddItemSerializer
from store.permissions import IsOwnerOrStaff
from store.filters    import OrderFilter
from store.pagination import StandardPagination


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class   = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, OrderingFilter]
    filterset_class    = OrderFilter
    ordering_fields    = ['created_at', 'total']
    ordering           = ['-created_at']
    http_method_names  = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        if self.request.user.is_staff:
            return (
                Order.objects
                .select_related('user')
                .prefetch_related('items__product')
                .all()
            )
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related('items__product')
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        order = self.get_object()
        if order.status != 'pending':
            return Response(
                {'error': f'Cannot modify an order with status "{order.status}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = AddItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product  = Product.objects.get(pk=serializer.validated_data['product_id'])
        quantity = serializer.validated_data['quantity']

        item, created = OrderItem.objects.get_or_create(
            order=order,
            product=product,
            defaults={'unit_price': product.price, 'quantity': quantity},
        )
        if not created:
            item.quantity += quantity
            item.save(update_fields=['quantity'])

        product.stock -= quantity
        product.save(update_fields=['stock'])
        order.calculate_total()

        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        order = self.get_object()
        if order.status != 'pending':
            return Response(
                {'error': 'Only pending orders can be confirmed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not order.items.exists():
            return Response(
                {'error': 'Cannot confirm an order with no items.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = 'confirmed'
        order.save(update_fields=['status'])
        return Response(OrderSerializer(order).data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAdminUser],
        url_path='update-status',
    )
    def update_status(self, request, pk=None):
        order         = self.get_object()
        new_status    = request.data.get('status')
        valid_statuses = [s[0] for s in Order.STATUS_CHOICES]

        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Valid options: {valid_statuses}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = new_status
        order.save(update_fields=['status'])
        return Response(OrderSerializer(order).data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAdminUser],
        url_path='stats',
    )
    def stats(self, request):
        from django.db.models import Count, Sum
        qs     = Order.objects.all()
        totals = qs.aggregate(
            total_orders = Count('id'),
            total_revenue = Sum('total'),
        )
        by_status = {
            s: qs.filter(status=s).count()
            for s, _ in Order.STATUS_CHOICES
        }
        return Response({
            'total_orders':   totals['total_orders'],
            'total_revenue':  float(totals['total_revenue'] or 0),
            'by_status':      by_status,
        })