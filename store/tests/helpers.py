# store/tests/helpers.py
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from store.models import Category, Product, Order, OrderItem


def create_user(username='user', email=None, password='Pass1234!', **kwargs):
    email = email or f'{username}@test.com'
    return User.objects.create_user(
        username=username, email=email, password=password, **kwargs
    )


def create_staff(username='staff', email=None, password='Admin1234!'):
    email = email or f'{username}@test.com'
    return User.objects.create_user(
        username=username, email=email, password=password, is_staff=True
    )


def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def auth_client(user):
    client = APIClient()
    access, _ = get_tokens(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    return client


def create_category(name='Electronics', slug='electronics', is_active=True):
    return Category.objects.create(name=name, slug=slug, is_active=is_active)


def create_product(name='Laptop', price=850, stock=10, category=None, is_active=True):
    if category is None:
        category = create_category()
    return Product.objects.create(
        name=name, price=price,
        stock=stock, category=category, is_active=is_active,
    )


def create_order(user, status='pending'):
    return Order.objects.create(user=user, status=status)


def add_item(order, product=None, quantity=1):
    if product is None:
        product = create_product()
    return OrderItem.objects.create(
        order=order,
        product=product,
        quantity=quantity,
        unit_price=product.price,
    )