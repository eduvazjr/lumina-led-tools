from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='gerencial_tester',
            password='test-password-only',
        )
        self.url = reverse('gerencial:dashboard')

    def test_dashboard_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_dashboard_renders_management_sections(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gerencial/dashboard.html')
        self.assertContains(response, 'class="kpi-grid"')
        self.assertContains(response, 'id="chartDist"')
        self.assertContains(response, 'id="chartVenc"')
        self.assertContains(response, 'class="filter-bar"')
        self.assertContains(response, 'vendor/chartjs/chart.umd.min.js')

    def test_dashboard_preserves_active_filters(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url, {'status': 'pago', 'periodo': '30'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="pago" selected')
        self.assertContains(response, 'value="30" selected')
