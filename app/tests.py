import json
from io import BytesIO
from unittest.mock import patch

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, RequestFactory
from django.urls import reverse
from app.models import User, Category, Home, Apartment


class RequirementsModelAndFilterTests(TestCase):
    def setUp(self):
        # 1 & 2. Create Category and Custom User
        self.cat1 = Category.objects.create(name='Turar joy majmuasi')
        self.cat2 = Category.objects.create(name='Biznes binosi')

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            role=User.Role.ORDINARY_USER
        )

        # 5 & 6. Home and Apartments
        self.home1 = Home.objects.create(name='Vatan', category=self.cat1)
        self.home2 = Home.objects.create(name='Rohat', category=self.cat2)

        self.apt1 = Apartment.objects.create(
            project=self.home1,
            rooms=2,
            floor=3,
            area=50.0,
            price=500000000
        )
        self.apt2 = Apartment.objects.create(
            project=self.home2,
            rooms=4,
            floor=8,
            area=110.0,
            price=1200000000
        )

    def test_custom_user_roles(self):
        self.assertEqual(self.user.role, 'ordinary_user')
        self.assertTrue(hasattr(self.user, 'avatar'))

    def test_category_creation(self):
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(self.home1.category.name, 'Turar joy majmuasi')

    def test_custom_auth_views(self):
        # Login test
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)

        # Logout test
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)

    def test_apartment_filters(self):
        # Filter by rooms
        res = self.client.get(reverse('home') + '?rooms=2')
        self.assertContains(res, '50,0 m²')
        self.assertNotContains(res, '110,0 m²')

        # Filter by floor
        res = self.client.get(reverse('home') + '?floor=8')
        self.assertContains(res, '110,0 m²')
        self.assertNotContains(res, '50,0 m²')

    def test_apartment_details_include_request_form(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'id="apartment-request-form"')
        self.assertContains(response, 'data-title="Vatan"')

    def test_contacts_and_partners_are_separate_pages(self):
        contacts = self.client.get(reverse('contacts'))
        partners = self.client.get(reverse('partners'))

        self.assertContains(contacts, 'Kompaniya rekvizitlari')
        self.assertContains(contacts, 'Sotuv ofislari')
        self.assertContains(partners, 'Hamkorlar uchun')
        self.assertContains(partners, 'hero-vooha-328.webp')
        self.assertContains(partners, 'hero-vatan-71.webp')
        self.assertContains(partners, 'hero-ramazon-46.webp')
        self.assertContains(partners, 'hero-muhabbat-387.webp')

        # Filter by price
        res = self.client.get(reverse('home') + '?min_price=1000000000')
        self.assertContains(res, '110,0 m²')
        self.assertNotContains(res, '50,0 m²')

    def test_profile_page_allows_email_avatar_and_password_update(self):
        self.client.login(username='testuser', password='password123')

        image = Image.new('RGB', (10, 10), color='blue')
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        avatar = SimpleUploadedFile(
            'avatar.png',
            buffer.getvalue(),
            content_type='image/png',
        )

        response = self.client.post(
            reverse('profile'),
            {
                'email': 'newmail@example.com',
                'avatar': avatar,
                'old_password': 'password123',
                'new_password1': 'NewPass123!',
                'new_password2': 'NewPass123!',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newmail@example.com')
        self.assertTrue(self.user.avatar)
        self.assertTrue(self.client.login(username='testuser', password='NewPass123!'))

    @patch('app.views.requests.post')
    def test_contact_form_notifies_admin_with_escaped_user_input(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'ok': True}

        with patch.dict('os.environ', {
            'TELEGRAM_BOT_TOKEN': 'test-token',
            'TELEGRAM_ADMIN_CHAT_ID': '987654321',
        }):
            request = RequestFactory().post(
                reverse('contact_submit'),
                {
                    'name': '<b>Ali</b>',
                    'phone': '+998901234567',
                    'message': '<i>Loyihada taklifim bor</i>',
                    'telegram_id': '123456789',
                    'telegram_username': 'alibek'
                }
            )
            response = __import__('app.views', fromlist=['contact_submit']).contact_submit(request)

        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertTrue(body['success'])
        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs['data']
        self.assertEqual(payload['chat_id'], '987654321')
        self.assertIn('&lt;b&gt;Ali&lt;/b&gt;', payload['text'])
        self.assertIn('&lt;i&gt;Loyihada taklifim bor&lt;/i&gt;', payload['text'])

