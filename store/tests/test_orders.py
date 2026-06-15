# store/tests/test_orders.py
from django.test import TestCase
from rest_framework import status

from .helpers import (
    create_user, create_staff, auth_client,
    create_product, create_order, add_item,
)


class OrderCRUDTests(TestCase):

    def setUp(self):
        self.user    = create_user('ivan')
        self.client  = auth_client(self.user)
        self.product = create_product(stock=20)

    def test_create_empty_order(self):
        resp = self.client.post('/api/orders/', {})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['status'], 'pending')
        self.assertEqual(resp.data['num_items'], 0)

    def test_add_item_reduces_stock(self):
        order       = create_order(self.user)
        stock_before = self.product.stock
        resp = self.client.post(
            f'/api/orders/{order.id}/add-item/',
            {'product_id': self.product.id, 'quantity': 3}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, stock_before - 3)

    def test_add_same_item_increments_quantity(self):
        order = create_order(self.user)
        self.client.post(
            f'/api/orders/{order.id}/add-item/',
            {'product_id': self.product.id, 'quantity': 2}
        )
        resp = self.client.post(
            f'/api/orders/{order.id}/add-item/',
            {'product_id': self.product.id, 'quantity': 3}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['num_items'], 1)

    def test_insufficient_stock_returns_400(self):
        order = create_order(self.user)
        resp  = self.client.post(
            f'/api/orders/{order.id}/add-item/',
            {'product_id': self.product.id, 'quantity': 999}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_order_with_items(self):
        order = create_order(self.user)
        add_item(order, self.product)
        resp  = self.client.post(f'/api/orders/{order.id}/confirm/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'confirmed')

    def test_confirm_empty_order_returns_400(self):
        order = create_order(self.user)
        resp  = self.client.post(f'/api/orders/{order.id}/confirm/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_add_item_to_confirmed_order(self):
        order = create_order(self.user, status='confirmed')
        resp  = self.client.post(
            f'/api/orders/{order.id}/add-item/',
            {'product_id': self.product.id, 'quantity': 1}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class OrderPermissionTests(TestCase):

    def setUp(self):
        self.user1   = create_user('julia')
        self.user2   = create_user('kevin')
        self.staff   = create_staff()
        self.product = create_product(stock=20)
        self.order   = create_order(self.user1)

    def test_user_cannot_see_other_users_order(self):
        resp = auth_client(self.user2).get(f'/api/orders/{self.order.id}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_can_see_any_order(self):
        resp = auth_client(self.staff).get(f'/api/orders/{self.order.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_staff_can_update_status(self):
        add_item(self.order, self.product)
        self.order.status = 'confirmed'
        self.order.save()
        resp = auth_client(self.staff).post(
            f'/api/orders/{self.order.id}/update-status/',
            {'status': 'shipped'}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'shipped')

    def test_regular_user_cannot_update_status(self):
        resp = auth_client(self.user1).post(
            f'/api/orders/{self.order.id}/update-status/',
            {'status': 'shipped'}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class OrderFilterTests(TestCase):

    def setUp(self):
        self.staff  = create_staff()
        self.client = auth_client(self.staff)
        user = create_user('laura')
        create_order(user, status='pending')
        create_order(user, status='confirmed')
        create_order(user, status='shipped')

    def test_filter_by_status(self):
        resp = self.client.get('/api/orders/?status=confirmed')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for order in resp.data['results']:
            self.assertEqual(order['status'], 'confirmed')

    def test_stats_staff_only(self):
        resp = self.client.get('/api/orders/stats/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for field in ['total_orders', 'total_revenue', 'by_status']:
            self.assertIn(field, resp.data)

    def test_stats_regular_user_returns_403(self):
        resp = auth_client(create_user('mario')).get('/api/orders/stats/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)