# store/serializers/order.py
from rest_framework import serializers
from store.models import Order, OrderItem, Product
from store.serializers.product import ProductSummarySerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSummarySerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model  = OrderItem
        fields = ['id', 'product', 'quantity', 'unit_price', 'subtotal']
        read_only_fields = ['id', 'unit_price']

    def get_subtotal(self, obj):
        return obj.subtotal


class OrderSerializer(serializers.ModelSerializer):
    items         = OrderItemSerializer(many=True, read_only=True)
    username      = serializers.CharField(source='user.username', read_only=True)
    num_items     = serializers.SerializerMethodField()

    class Meta:
        model  = Order
        fields = [
            'id', 'username', 'status', 'total',
            'num_items', 'items', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'total', 'created_at', 'updated_at']

    def get_num_items(self, obj):
        return obj.items.count()


class AddItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity   = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        try:
            Product.objects.get(pk=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError(
                f'Product {value} not found or inactive.'
            )
        return value

    def validate(self, data):
        product = Product.objects.get(pk=data['product_id'])
        if product.stock < data['quantity']:
            raise serializers.ValidationError(
                f'Insufficient stock: only {product.stock} units available.'
            )
        return data
        