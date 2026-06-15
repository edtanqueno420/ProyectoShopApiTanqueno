# store/serializers/product.py
from rest_framework import serializers
from store.models import Product
from store.serializers.category import CategorySerializer


class ProductSummarySerializer(serializers.ModelSerializer):

    class Meta:
        model  = Product
        fields = ['id', 'name', 'price', 'stock', 'is_active']


class ProductSerializer(serializers.ModelSerializer):
    category       = CategorySerializer(read_only=True)
    category_id    = serializers.PrimaryKeyRelatedField(
        source='category',
        write_only=True,
        queryset=Product.objects.none(),
    )
    price_with_tax = serializers.SerializerMethodField()
    in_stock       = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'description',
            'price', 'price_with_tax',
            'stock', 'in_stock', 'is_active',
            'category', 'category_id',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from store.models import Category
        self.fields['category_id'].queryset = Category.objects.filter(is_active=True)

    def get_price_with_tax(self, obj):
        return obj.price_with_tax

    def get_in_stock(self, obj):
        return obj.in_stock

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be greater than 0.')
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError('Stock cannot be negative.')
        return value