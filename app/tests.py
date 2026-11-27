import json
import re
from datetime import timedelta
from io import BytesIO, StringIO
from unittest.mock import patch

from PIL import Image
from django.core import mail
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone
from app.models import User, Category, Home, Apartment, ApartmentReservation, BotUser, PasswordResetCode, SalesOffice
from app.management.commands.runbot import TelegramBot


class PasswordResetDeliveryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reset-user',
            email='reset@example.com',
            password='OldPassword123',
            telegram_id='123456789',
        )

    def test_profile_saves_email_and_telegram_id(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {
            'email': 'new-reset@example.com',
            'telegram_id': '987654321',
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'new-reset@example.com')
        self.assertEqual(self.user.telegram_id, '987654321')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch('app.views.send_password_reset_code_telegram', return_value=(False, 'Telegram chat ID topilmadi.'))
    def test_password_reset_request_sends_email_code(self, telegram_send):
        response = self.client.post(reverse('password_reset_request'), {
            'email': self.user.email,
        })
        self.assertRedirects(response, reverse('password_reset_confirm'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        reset_code = PasswordResetCode.objects.get(user=self.user, is_used=False)
        self.assertIn(reset_code.code, mail.outbox[0].body)


class TelegramFeatureTests(TestCase):
    def setUp(self):
        self.bot = TelegramBot(token='test-token')

    @patch.object(TelegramBot, 'send_message')
    def test_installment_calculator_infers_percentage_from_down_payment(self, send_message):
        chat_id = 123456
        self.bot.handle_calc_fixed(chat_id, 300000000)
        self.assertEqual(self.bot.user_states[chat_id]['state'], 'calc_down_amount')
        self.bot.handle_calc_select_period(chat_id, 75000000)
        self.assertEqual(self.bot.user_states[chat_id]['pct'], 25)
        self.assertEqual(self.bot.user_states[chat_id]['down_sum'], 75000000)
        self.assertIn('75 000 000', send_message.call_args.args[1])
        self.assertIn('25%', send_message.call_args.args[1])

    def test_main_keyboard_has_location_request_button(self):
        keyboard = self.bot.get_main_keyboard(123456)
        buttons = [button for row in keyboard['keyboard'] for button in row]
        location_button = next(button for button in buttons if button.get('request_location'))
        self.assertEqual(location_button['text'], '📍 Yaqin manzilni topish')

    @patch.object(TelegramBot, 'send_location')
    @patch.object(TelegramBot, 'send_message')
    def test_location_finds_nearest_office_and_project(self, send_message, send_location):
        office = SalesOffice.objects.create(
            name='Yaqin ofis',
            address='Toshkent',
            latitude=41.311081,
            longitude=69.240562,
        )
        home = Home.objects.create(
            name='Yaqin loyiha',
            latitude=41.320000,
            longitude=69.250000,
        )
        self.bot.handle_nearest_location(123456, 41.311081, 69.240562)
        self.assertGreaterEqual(send_location.call_count, 2)
        sent_text = send_message.call_args.args[1]
        self.assertIn(office.name, sent_text)
        self.assertIn(home.name, sent_text)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
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

        res = self.client.get(
            reverse('home') + f'?project={self.home1.pk}&floor_min=2&floor_max=4'
        )
        self.assertContains(res, '50,0 m²')
        self.assertNotContains(res, '110,0 m²')

        ajax_res = self.client.get(
            reverse('home') + f'?project={self.home2.pk}&floor_min=8&floor_max=8&ajax=1',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(ajax_res.json()['count'], 1)

    def test_apartment_details_include_request_form(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'id="apartment-reservation-request-form"')
        self.assertContains(response, 'data-title="Vatan"')

    def test_project_status_can_be_loaded_without_full_page_navigation(self):
        response = self.client.get(
            reverse('home') + '?status=in_progress&projects_ajax=1&ajax=1',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertIn('project-grid', response.json()['html'])
        self.assertContains(
            self.client.get(reverse('home')),
            'data-project-link',
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_apartment_reservation_requires_email_code_and_marks_unit_reserved(self):
        response = self.client.post(reverse('apartment_reservation_request'), {
            'apartment_id': self.apt1.pk,
            'name': 'Ali Valiyev',
            'email': 'ali@example.com',
            'phone': '+998901234567',
        })

        self.assertEqual(response.status_code, 200)
        reservation_id = response.json()['reservation_id']
        self.apt1.refresh_from_db()
        self.assertEqual(self.apt1.availability, Apartment.Availability.RESERVED)
        self.assertEqual(len(mail.outbox), 1)
        code = re.search(r'\b\d{6}\b', mail.outbox[0].body).group()

        confirmation = self.client.post(reverse('apartment_reservation_confirm'), {
            'reservation_id': reservation_id,
            'code': code,
        })

        self.assertEqual(confirmation.status_code, 200)
        self.assertTrue(confirmation.json()['success'])
        self.apt1.refresh_from_db()
        self.assertEqual(self.apt1.availability, Apartment.Availability.RESERVED)
        self.assertEqual(
            ApartmentReservation.objects.get(public_id=reservation_id).status,
            ApartmentReservation.Status.CONFIRMED,
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_unavailable_apartment_cannot_be_reserved_and_bad_codes_release_after_five_tries(self):
        self.apt1.availability = Apartment.Availability.SOLD
        self.apt1.save(update_fields=['availability'])
        request_data = {
            'apartment_id': self.apt1.pk,
            'name': 'Ali Valiyev',
            'email': 'ali@example.com',
            'phone': '+998901234567',
        }
        unavailable = self.client.post(reverse('apartment_reservation_request'), request_data)
        self.assertEqual(unavailable.status_code, 409)

        self.apt1.availability = Apartment.Availability.AVAILABLE
        self.apt1.save(update_fields=['availability'])
        requested = self.client.post(reverse('apartment_reservation_request'), request_data)
        reservation_id = requested.json()['reservation_id']
        for _ in range(5):
            invalid = self.client.post(reverse('apartment_reservation_confirm'), {
                'reservation_id': reservation_id,
                'code': '000000',
            })
        self.assertEqual(invalid.status_code, 400)
        self.apt1.refresh_from_db()
        self.assertEqual(self.apt1.availability, Apartment.Availability.AVAILABLE)
        self.assertEqual(
            ApartmentReservation.objects.get(public_id=reservation_id).status,
            ApartmentReservation.Status.EXPIRED,
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_expired_reservation_code_releases_apartment(self):
        requested = self.client.post(reverse('apartment_reservation_request'), {
            'apartment_id': self.apt1.pk,
            'name': 'Ali Valiyev',
            'email': 'ali@example.com',
            'phone': '+998901234567',
        })
        reservation_id = requested.json()['reservation_id']
        reservation = ApartmentReservation.objects.get(public_id=reservation_id)
        reservation.expires_at = timezone.now() - timedelta(seconds=1)
        reservation.save(update_fields=['expires_at'])

        response = self.client.post(reverse('apartment_reservation_confirm'), {
            'reservation_id': reservation_id,
            'code': re.search(r'\b\d{6}\b', mail.outbox[0].body).group(),
        })

        self.assertEqual(response.status_code, 410)
        self.apt1.refresh_from_db()
        self.assertEqual(self.apt1.availability, Apartment.Availability.AVAILABLE)

    @patch('app.views.send_apartment_reservation_code_email', return_value=0)
    def test_email_delivery_failure_does_not_leave_apartment_reserved(self, mock_send_email):
        response = self.client.post(reverse('apartment_reservation_request'), {
            'apartment_id': self.apt1.pk,
            'name': 'Ali Valiyev',
            'email': 'ali@example.com',
            'phone': '+998901234567',
        })

        self.assertEqual(response.status_code, 503)
        self.assertNotIn('code', response.json())
        self.apt1.refresh_from_db()
        self.assertEqual(self.apt1.availability, Apartment.Availability.AVAILABLE)
        self.assertEqual(
            ApartmentReservation.objects.get().status,
            ApartmentReservation.Status.EXPIRED,
        )
        mock_send_email.assert_called_once()

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend')
    def test_console_email_backend_is_not_reported_as_successful_delivery(self):
        response = self.client.post(reverse('apartment_reservation_request'), {
            'apartment_id': self.apt1.pk,
            'name': 'Ali Valiyev',
            'email': 'ali@example.com',
            'phone': '+998901234567',
        })

        self.assertEqual(response.status_code, 503)
        self.apt1.refresh_from_db()
        self.assertEqual(self.apt1.availability, Apartment.Availability.AVAILABLE)

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


class TelegramBotApartmentPaginationTests(TestCase):
    def setUp(self):
        self.project = Home.objects.create(name='Pagination project')
        other_project = Home.objects.create(name='Other project')
        for index in range(6):
            Apartment.objects.create(
                project=self.project,
                rooms=2,
                floor=index + 1,
                area=50,
                price=500000000,
            )
        Apartment.objects.create(
            project=other_project,
            rooms=2,
            floor=1,
            area=50,
            price=500000000,
        )
        self.bot = TelegramBot(token='test-token')

    @patch.object(TelegramBot, 'send_message')
    def test_project_and_room_filters_are_kept_on_next_page(self, mock_send_message):
        self.bot.handle_apartments_list(
            '123456789',
            project_id=self.project.id,
            rooms=2,
        )

        markup = mock_send_message.call_args.kwargs['reply_markup']
        next_page = markup['inline_keyboard'][-2][0]['callback_data']
        self.assertEqual(next_page, f'aptpage_proj_{self.project.id}_rm_2_p2')
        self.assertEqual(
            self.bot._parse_aptpage_callback(next_page),
            {'project_id': self.project.id, 'rooms': 2, 'page': 2},
        )

    @patch.object(TelegramBot, 'send_message')
    def test_broadcast_report_counts_only_successful_sends(self, mock_send_message):
        BotUser.objects.create(telegram_id='111')
        BotUser.objects.create(telegram_id='222')
        mock_send_message.side_effect = [
            {'ok': True},
            {'ok': False, 'description': 'blocked'},
            {'ok': True},
        ]

        self.bot.broadcast_message('admin', 'Announcement')

        report = mock_send_message.call_args.args[1]
        self.assertIn('1 ta foydalanuvchiga yuborildi', report)
        self.assertIn('1 ta foydalanuvchiga yuborilmadi', report)


class TelegramWebhookTests(TestCase):
    @patch.object(TelegramBot, 'answer_callback_query')
    @patch.object(TelegramBot, 'send_message')
    def test_webhook_checks_secret_and_persists_conversation_state(
        self,
        mock_send_message,
        mock_answer_callback,
    ):
        update = {
            'callback_query': {
                'id': 'callback-1',
                'from': {'id': 123456789, 'first_name': 'Ali'},
                'message': {'chat': {'id': 123456789}},
                'data': 'calc_pr_custom',
            }
        }

        with patch.dict('os.environ', {
            'TELEGRAM_BOT_TOKEN': 'test-token',
            'TELEGRAM_WEBHOOK_SECRET': 'test-secret',
        }):
            rejected = self.client.post(
                reverse('telegram_webhook'),
                data=json.dumps(update),
                content_type='application/json',
                HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='wrong-secret',
            )
            self.assertEqual(rejected.status_code, 403)
            self.assertFalse(BotUser.objects.exists())

            accepted = self.client.post(
                reverse('telegram_webhook'),
                data=json.dumps(update),
                content_type='application/json',
                HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='test-secret',
            )
            follow_up = self.client.post(
                reverse('telegram_webhook'),
                data=json.dumps({
                    'message': {
                        'chat': {'id': 123456789},
                        'from': {'id': 123456789, 'first_name': 'Ali'},
                        'text': '500000000',
                    }
                }),
                content_type='application/json',
                HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='test-secret',
            )
            down_payment = self.client.post(
                reverse('telegram_webhook'),
                data=json.dumps({
                    'message': {
                        'chat': {'id': 123456789},
                        'from': {'id': 123456789, 'first_name': 'Ali'},
                        'text': '100000000',
                    }
                }),
                content_type='application/json',
                HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='test-secret',
            )
            computed = self.client.post(
                reverse('telegram_webhook'),
                data=json.dumps({
                    'callback_query': {
                        'id': 'callback-2',
                        'from': {'id': 123456789, 'first_name': 'Ali'},
                        'message': {'chat': {'id': 123456789}},
                        'data': 'calc_per_36',
                    }
                }),
                content_type='application/json',
                HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='test-secret',
            )

        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(follow_up.status_code, 200)
        self.assertEqual(down_payment.status_code, 200)
        self.assertEqual(computed.status_code, 200)
        bot_user = BotUser.objects.get(telegram_id='123456789')
        self.assertEqual(bot_user.conversation_state['state'], 'awaiting_contact')
        self.assertIn('Narx=500 000 000', bot_user.conversation_state['note'])
        self.assertIn("Boshlang'ich=20%", bot_user.conversation_state['note'])
        self.assertIn('Muddat=36 oy', bot_user.conversation_state['note'])
        self.assertEqual(mock_answer_callback.call_count, 2)
        self.assertEqual(mock_send_message.call_count, 4)

    @override_settings(SITE_URL='https://demo.pythonanywhere.com')
    @patch.object(TelegramBot, 'call_api')
    def test_management_command_sets_webhook_with_configured_secret(self, mock_call_api):
        mock_call_api.side_effect = [
            {'ok': True, 'result': {'username': 'demo_bot'}},
            {'ok': True, 'result': {'url': ''}},
            {'ok': True, 'result': True},
        ]
        output = StringIO()

        with patch.dict('os.environ', {
            'TELEGRAM_BOT_TOKEN': 'test-token',
            'TELEGRAM_WEBHOOK_SECRET': 'test-secret',
        }):
            call_command('runbot', '--set-webhook', stdout=output)

        mock_call_api.assert_called_with('setWebhook', {
            'url': 'https://demo.pythonanywhere.com/telegram/webhook/',
            'secret_token': 'test-secret',
            'allowed_updates': json.dumps(['message', 'callback_query']),
        })

