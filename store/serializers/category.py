# store/serializers/category.py — reemplazar CategorySerializer
from rest_framework import serializers
from django.utils.text import slugify
from store.models import Category


class CategorySerializer(serializers.ModelSerializer):
    total_products = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = [
            'id', 'name', 'slug', 'description',
            'is_active', 'total_products', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_total_products(self, obj):
        return obj.products.filter(is_active=True).count()

    def validate_slug(self, value):
        return slugify(value)

    def validate_name(self, value):
        qs = Category.objects.filter(name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('A category with this name already exists.')
        return value