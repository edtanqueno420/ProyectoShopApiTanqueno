# store/tests/test_categories.py
from django.test import TestCase
from rest_framework import status

from .helpers import create_user, create_staff, auth_client, create_category


class CategoryPermissionTests(TestCase):

    def setUp(self):
        self.user     = create_user('eve')
        self.staff    = create_staff()
        self.category = create_category()

    def test_authenticated_user_can_list(self):
        resp = auth_client(self.user).get('/api/categories/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_returns_401(self):
        from rest_framework.test import APIClient
        resp = APIClient().get('/api/categories/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_create(self):
        resp = auth_client(self.user).post('/api/categories/', {
            'name': 'Test', 'slug': 'test'
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_create(self):
        resp = auth_client(self.staff).post('/api/categories/', {
            'name': 'Home', 'slug': 'home', 'is_active': True
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_staff_can_delete(self):
        resp = auth_client(self.staff).delete(f'/api/categories/{self.category.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


class CategoryFilterTests(TestCase):

    def setUp(self):
        self.client = auth_client(create_user('filters'))
        create_category('Electronics', 'electronics', is_active=True)
        create_category('Clothing',    'clothing',    is_active=False)

    def test_filter_by_active(self):
        resp = self.client.get('/api/categories/?is_active=true')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['name'], 'Electronics')

    def test_search_by_name(self):
        resp = self.client.get('/api/categories/?search=electro')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)

    def test_stats_returns_expected_fields(self):
        resp = self.client.get('/api/categories/stats/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for field in ['total', 'active', 'inactive', 'detail']:
            self.assertIn(field, resp.data)