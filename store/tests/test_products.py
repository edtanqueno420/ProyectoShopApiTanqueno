# store/tests/test_products.py
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .helpers import create_user, create_staff, auth_client, create_category, create_product


class ProductPermissionTests(TestCase):

    def setUp(self):
        self.user    = create_user('frank')
        self.staff   = create_staff()
        self.cat     = create_category()
        self.product = create_product(category=self.cat)

    def test_authenticated_can_list(self):
        resp = auth_client(self.user).get('/api/products/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)

    def test_unauthenticated_returns_401(self):
        resp = APIClient().get('/api/products/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_create(self):
        resp = auth_client(self.user).post('/api/products/', {
            'name': 'Test', 'price': '10.00',
            'stock': 5, 'category_id': self.cat.id,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_create(self):
        resp = auth_client(self.staff).post('/api/products/', {
            'name': 'Keyboard', 'price': '79.00',
            'stock': 12, 'category_id': self.cat.id,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_price_with_tax_is_15_percent(self):
        resp = auth_client(self.user).get(f'/api/products/{self.product.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        expected = round(float(self.product.price) * 1.15, 2)
        self.assertEqual(float(resp.data['price_with_tax']), expected)


class ProductFilterTests(TestCase):

    def setUp(self):
        self.client = auth_client(create_user('gina'))
        cat = create_category()
        create_product('Laptop',   price=850, stock=5,  category=cat)
        create_product('Cheap',    price=20,  stock=0,  category=cat)
        create_product('Inactive', price=50,  stock=10, category=cat, is_active=False)

    def test_filter_by_max_price(self):
        resp = self.client.get('/api/products/?price_max=100')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['name'], 'Cheap')

    def test_filter_by_min_stock(self):
        resp = self.client.get('/api/products/?stock_min=1')
        names = [p['name'] for p in resp.data['results']]
        self.assertIn('Laptop', names)
        self.assertNotIn('Cheap', names)

    def test_search_by_name(self):
        resp = self.client.get('/api/products/?search=lapt')
        self.assertEqual(resp.data['count'], 1)

    def test_available_is_public(self):
        resp = APIClient().get('/api/products/available/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [p['name'] for p in resp.data['results']]
        self.assertIn('Laptop', names)
        self.assertNotIn('Cheap', names)


class ProductActionTests(TestCase):

    def setUp(self):
        self.staff   = create_staff()
        self.user    = create_user('henry')
        self.product = create_product(stock=10)

    def test_restock_adds_stock(self):
        resp = auth_client(self.staff).post(
            f'/api/products/{self.product.id}/restock/',
            {'quantity': 5}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['new_stock'], 15)

    def test_restock_regular_user_returns_403(self):
        resp = auth_client(self.user).post(
            f'/api/products/{self.product.id}/restock/',
            {'quantity': 5}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_restock_invalid_quantity(self):
        resp = auth_client(self.staff).post(
            f'/api/products/{self.product.id}/restock/',
            {'quantity': -1}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stats_returns_expected_fields(self):
        resp = auth_client(self.user).get('/api/products/stats/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for field in ['total_active', 'avg_price', 'total_stock', 'out_of_stock']:
            self.assertIn(field, resp.data)