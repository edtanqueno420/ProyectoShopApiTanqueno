# store/tests/test_users.py
from django.test import TestCase
from rest_framework import status

from .helpers import create_user, create_staff, auth_client


class ProfileTests(TestCase):

    def setUp(self):
        self.user   = create_user('carlos')
        self.client = auth_client(self.user)

    def test_get_own_profile(self):
        resp = self.client.get('/api/users/profile/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['username'], 'carlos')

    def test_update_own_profile(self):
        resp = self.client.patch('/api/users/profile/', {'first_name': 'Carlos'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['first_name'], 'Carlos')

    def test_change_password_success(self):
        resp = self.client.post('/api/users/change-password/', {
            'current_password': 'Pass1234!',
            'new_password':     'New5678!',
            'new_password2':    'New5678!',
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_change_password_wrong_current(self):
        resp = self.client.post('/api/users/change-password/', {
            'current_password': 'Wrong!',
            'new_password':     'New5678!',
            'new_password2':    'New5678!',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class UserStaffTests(TestCase):

    def setUp(self):
        self.staff  = create_staff()
        self.user   = create_user('diana')
        self.client = auth_client(self.staff)

    def test_staff_can_list_users(self):
        resp = self.client.get('/api/users/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)

    def test_regular_user_cannot_list(self):
        resp = auth_client(self.user).get('/api/users/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_toggle_active(self):
        resp = self.client.post(f'/api/users/{self.user.id}/toggle-active/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('is_active', resp.data)

    def test_staff_can_get_stats(self):
        resp = self.client.get('/api/users/stats/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for field in ['total', 'active', 'inactive', 'staff']:
            self.assertIn(field, resp.data)

    def test_filter_by_is_staff(self):
        resp = self.client.get('/api/users/?is_staff=true')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for u in resp.data['results']:
            self.assertTrue(u['is_staff'])