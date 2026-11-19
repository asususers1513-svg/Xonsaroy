import html
import logging
import os
import secrets
from datetime import timedelta

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Apartment, ApartmentImage, ApartmentReservation, Category, Client, Home, Material, SalesOffice, User, PasswordResetCode, Lead, BotUser
from .forms import (
    UserRegisterForm, UserLoginForm, UserProfileForm, ContactRequestForm, OptionalPasswordChangeForm,
    PasswordResetRequestForm, PasswordResetConfirmForm, ApartmentReservationRequestForm,
    ApartmentReservationConfirmForm,
)

logger = logging.getLogger(__name__)


def send_telegram_message(chat_id, text):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
    if not bot_token:
        return False, 'Telegram bot tokeni serverda sozlanmagan.'
    if not chat_id:
        return False, 'Telegram ID not found.'

    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,
    }
    try:
        response = requests.post(
            f'https://api.telegram.org/bot{bot_token}/sendMessage',
            data=payload,
            timeout=15,
        )
    except requests.RequestException as exc:
        logger.error("Telegram xabarini yuborib bo'lmadi (%s).", type(exc).__name__)
        return False, 'Telegram serveriga ulanib bo‘lmadi.'
    resp = response.json() if response.headers.get('Content-Type', '').startswith('application/json') else {}
    if resp.get('ok'):
        return True, 'Xabar yuborildi.'
    return False, resp.get('description', 'Telegramga xabar yuborishda xatolik yuz berdi.')


def contact_submit(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

    form = ContactRequestForm(request.POST)
    if not form.is_valid():
        errors = form.errors.get_json_data()
        first_error = next(iter(errors.values()), [{'message': 'Ma`lumot to`liq kiritilmadi.'}])[0]['message']
        return JsonResponse({'success': False, 'message': first_error}, status=400)

    cleaned = form.cleaned_data
    telegram_id = str(cleaned.get('telegram_id') or '').strip()
    telegram_username = str(cleaned.get('telegram_username') or '').strip()
    recipient_chat = os.getenv('TELEGRAM_ADMIN_CHAT_ID', '').strip()

    text = (
        '<b>Yangi ariza</b>\n'
        f'Ism: {html.escape(cleaned["name"])}\n'
        f'Telefon: {html.escape(cleaned["phone"])}\n'
        f'Telegram: @{html.escape(telegram_username)} ({html.escape(telegram_id or "noma`lum")})\n\n'
        f'{html.escape(cleaned["message"])}'
    )

    Lead.objects.create(
        name=cleaned["name"],
        phone=cleaned["phone"],
        telegram_id=telegram_id or None,
        telegram_username=telegram_username or None,
        source=Lead.Source.WEBSITE,
        note=cleaned.get("message", "")
    )

    if not recipient_chat:
        return JsonResponse({
            'success': True,
            'warning': True,
            'message': 'Arizangiz qabul qilindi. Admin Telegram xabarnomasini sozlash kerak.'
        })

    sent, message = send_telegram_message(recipient_chat, text)
    if sent:
        return JsonResponse({'success': True, 'message': 'Arizangiz muvaffaqiyatli yuborildi.'})
    return JsonResponse({
        'success': True,
        'warning': True,
        'message': f'Arizangiz bazaga saqlandi, ammo Telegramga yuborilmadi: {message}',
    })


def home(request):
	expire_pending_apartment_reservations()
	selected_status = request.GET.get('status', Home.Status.IN_PROGRESS)
	selected_category = request.GET.get('category', 'all')
	
	# Filter params for Apartments
	filter_rooms = request.GET.get('rooms')
	filter_floor = request.GET.get('floor')
	filter_min_area = request.GET.get('min_area')
	filter_max_area = request.GET.get('max_area')
	filter_min_price = request.GET.get('min_price')
	filter_max_price = request.GET.get('max_price')
	filter_availability = request.GET.get('availability')

	categories = Category.objects.all()
	all_homes = Home.objects.select_related('category').prefetch_related('apartments').order_by('id')
	homes = all_homes

	if selected_status != 'all' and selected_status in Home.Status.values:
		homes = homes.filter(status=selected_status)

	if selected_category != 'all' and selected_category.isdigit():
		homes = homes.filter(category_id=selected_category)

	apartments = Apartment.objects.filter(is_active=True).select_related('project', 'project__category')

	if selected_category != 'all' and selected_category.isdigit():
		apartments = apartments.filter(project__category_id=selected_category)

	if filter_rooms and filter_rooms.isdigit():
		room_count = int(filter_rooms)
		apartments = apartments.filter(rooms__gte=room_count) if room_count == 4 else apartments.filter(rooms=room_count)

	if filter_availability in Apartment.Availability.values:
		apartments = apartments.filter(availability=filter_availability)

	if filter_floor and filter_floor.isdigit():
		apartments = apartments.filter(floor=int(filter_floor))

	if filter_min_area:
		try:
			apartments = apartments.filter(area__gte=float(filter_min_area))
		except ValueError:
			pass

	if filter_max_area:
		try:
			apartments = apartments.filter(area__lte=float(filter_max_area))
		except ValueError:
			pass

	if filter_min_price:
		try:
			apartments = apartments.filter(price__gte=float(filter_min_price))
		except ValueError:
			pass

	if filter_max_price:
		try:
			apartments = apartments.filter(price__lte=float(filter_max_price))
		except ValueError:
			pass
	apartments = list(apartments)
	for apartment in apartments:
		apartment.display_title = apartment.project.name if apartment.project_id else 'Xonadon'
		try:
			area_val = float(apartment.area) if apartment.area else 0
			price_val = float(apartment.price) if apartment.price else 0
			if area_val > 0 and price_val > 0:
				apartment.m2_price = int(round(price_val / area_val))
				apartment.down_payment = int(round(price_val * 0.15))
				apartment.monthly_payment = int(round((price_val * 0.85) / 36))
			else:
				apartment.m2_price = 0
				apartment.down_payment = 0
				apartment.monthly_payment = 0
		except Exception:
			apartment.m2_price = 0
			apartment.down_payment = 0
			apartment.monthly_payment = 0

	floorplan_apartments = []
	for apartment in Apartment.objects.filter(is_active=True).select_related('project', 'project__category'):
		image = apartment.image_url or (apartment.image.url if apartment.image else '')
		if apartment.project_id:
			image = image or apartment.project.hero_image_url or (
				apartment.project.hero_image.url if apartment.project.hero_image else ''
			)
		floorplan_apartments.append({
			'id': apartment.id,
			'unit_number': apartment.unit_number or f'#{apartment.id}',
			'project_id': apartment.project_id,
			'project_name': apartment.project.name if apartment.project_id else 'Xonadon',
			'rooms': apartment.rooms,
			'floor': apartment.floor,
			'area': str(apartment.area),
			'price': str(int(apartment.price)),
			'availability': apartment.availability,
			'category': apartment.project.category.name if apartment.project_id and apartment.project.category_id else 'Turar joy majmuasi',
			'status': apartment.project.get_status_display() if apartment.project_id else 'Jarayonda',
			'description': apartment.description or (apartment.project.description if apartment.project_id else ''),
			'image': image,
		})
	inventory_projects = Home.objects.filter(apartments__is_active=True).distinct().order_by('name')

	if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
		if request.GET.get('projects_ajax') == '1':
			project_grid_html = render_to_string('app/_project_grid.html', {
				'homes': homes,
			}, request=request)
			return JsonResponse({
				'success': True,
				'html': project_grid_html,
			})
		grid_html = render_to_string('app/_apartment_grid.html', {
			'apartments': apartments,
		}, request=request)
		return JsonResponse({
			'success': True,
			'count': len(apartments),
			'html': grid_html,
		})

	return render(request, 'app/home.html', {
		'categories': categories,
		'homes': homes,
		'projects': all_homes,
		'inventory_projects': inventory_projects,
		'floorplan_apartments': floorplan_apartments,
		'featured_home': homes.first() or all_homes.first(),
		'statuses': Home.Status.choices,
		'selected_status': selected_status,
		'selected_category': selected_category,
		'apartments': apartments,
		'materials': Material.objects.all(),
		'clients': Client.objects.all(),
		'offices': SalesOffice.objects.all(),
		'filters': {
			'rooms': filter_rooms or '',
			'floor': filter_floor or '',
			'min_area': filter_min_area or '',
			'max_area': filter_max_area or '',
			'min_price': filter_min_price or '',
			'max_price': filter_max_price or '',
			'availability': filter_availability or '',
		}
	})


def send_apartment_reservation_code_email(reservation, code):
	if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
		raise ImproperlyConfigured('SMTP email sozlamalarini kiriting; konsol backend xatni yetkazmaydi.')
	subject = 'Xon Saroy — bronni tasdiqlash kodi'
	context = {'code': code, 'reservation': reservation, 'expires_minutes': 10}
	html_content = render_to_string('emails/apartment_reservation_code.html', context)
	text_content = (
		f"Assalomu alaykum, {reservation.name}!\n\n"
		f"{reservation.apartment.project or 'Xon Saroy'} loyihasidagi "
		f"{reservation.apartment.rooms} xonali xonadon bronini tasdiqlash kodi: {code}\n\n"
		"Ushbu kod 10 daqiqa davomida amal qiladi."
	)
	email = EmailMultiAlternatives(
		subject=subject,
		body=text_content,
		from_email=settings.DEFAULT_FROM_EMAIL,
		to=[reservation.email],
	)
	email.attach_alternative(html_content, 'text/html')
	return email.send(fail_silently=False)


def expire_pending_apartment_reservations():
	now = timezone.now()
	with transaction.atomic():
		expired = ApartmentReservation.objects.select_for_update().filter(
			status=ApartmentReservation.Status.PENDING,
			expires_at__lte=now,
		)
		for reservation in expired:
			reservation.status = ApartmentReservation.Status.EXPIRED
			reservation.save(update_fields=['status'])
			has_live_reservation = ApartmentReservation.objects.filter(
				apartment_id=reservation.apartment_id,
				status=ApartmentReservation.Status.PENDING,
				expires_at__gt=now,
			).exists()
			if not has_live_reservation:
				Apartment.objects.filter(
					pk=reservation.apartment_id,
					availability=Apartment.Availability.RESERVED,
				).update(availability=Apartment.Availability.AVAILABLE)


def release_apartment_reservation(reservation):
	reservation.status = ApartmentReservation.Status.EXPIRED
	reservation.save(update_fields=['status'])
	has_live_reservation = ApartmentReservation.objects.filter(
		apartment_id=reservation.apartment_id,
		status=ApartmentReservation.Status.PENDING,
		expires_at__gt=timezone.now(),
	).exists()
	if not has_live_reservation:
		Apartment.objects.filter(
			pk=reservation.apartment_id,
			availability=Apartment.Availability.RESERVED,
		).update(availability=Apartment.Availability.AVAILABLE)


@require_POST
def apartment_reservation_request_view(request):
	form = ApartmentReservationRequestForm(request.POST)
	if not form.is_valid():
		return JsonResponse({
			'success': False,
			'message': next(iter(form.errors.values()))[0],
		}, status=400)

	cleaned = form.cleaned_data
	now = timezone.now()
	expire_pending_apartment_reservations()
	recent_requests = ApartmentReservation.objects.filter(
		email__iexact=cleaned['email'],
		created_at__gte=now - timedelta(minutes=10),
	).count()
	if recent_requests >= 3:
		return JsonResponse({
			'success': False,
			'message': 'Yangi tasdiqlash kodini so‘rash limiti tugadi. Birozdan keyin qayta urinib ko‘ring.',
		}, status=429)

	try:
		apartment = Apartment.objects.select_related('project').get(
			pk=cleaned['apartment_id'],
			is_active=True,
		)
	except Apartment.DoesNotExist:
		return JsonResponse({'success': False, 'message': 'Xonadon topilmadi.'}, status=404)
	if apartment.availability != Apartment.Availability.AVAILABLE:
		return JsonResponse({
			'success': False,
			'message': 'Bu xonadon hozir bo‘sh emas. Boshqa xonadon tanlang.',
		}, status=409)

	code = f'{secrets.randbelow(900000) + 100000}'
	with transaction.atomic():
		claimed = Apartment.objects.filter(
			pk=apartment.pk,
			is_active=True,
			availability=Apartment.Availability.AVAILABLE,
		).update(availability=Apartment.Availability.RESERVED)
		if not claimed:
			return JsonResponse({
				'success': False,
				'message': 'Bu xonadon hozirgina band qilindi. Boshqa xonadon tanlang.',
			}, status=409)
		reservation = ApartmentReservation.objects.create(
			apartment=apartment,
			name=cleaned['name'],
			email=cleaned['email'],
			phone=cleaned['phone'],
			code_hash=make_password(code),
			expires_at=now + timedelta(minutes=10),
		)

	try:
		email_sent = send_apartment_reservation_code_email(reservation, code)
	except Exception:
		logger.exception('Xonadon bron kodi email orqali yuborilmadi.')
		email_sent = 0
	if not email_sent:
		with transaction.atomic():
			reservation = ApartmentReservation.objects.select_for_update().get(pk=reservation.pk)
			release_apartment_reservation(reservation)
		return JsonResponse({
			'success': False,
			'message': 'Tasdiqlash kodi emailingizga yuborilmadi. Email sozlamalarini tekshirib, qayta urinib ko‘ring.',
		}, status=503)

	return JsonResponse({
		'success': True,
		'reservation_id': str(reservation.public_id),
		'message': 'Tasdiqlash kodi emailingizga yuborildi. Kod 10 daqiqa amal qiladi.',
	})


@require_POST
def apartment_reservation_confirm_view(request):
	form = ApartmentReservationConfirmForm(request.POST)
	if not form.is_valid():
		return JsonResponse({
			'success': False,
			'message': 'Bron raqami yoki 6 xonali tasdiqlash kodi noto‘g‘ri.',
		}, status=400)

	with transaction.atomic():
		try:
			reservation = ApartmentReservation.objects.select_for_update().select_related('apartment').get(
				public_id=form.cleaned_data['reservation_id'],
			)
		except ApartmentReservation.DoesNotExist:
			return JsonResponse({'success': False, 'message': 'Bron topilmadi.'}, status=404)

		if reservation.status != ApartmentReservation.Status.PENDING:
			return JsonResponse({
				'success': False,
				'message': 'Ushbu bron faol emas. Xonadonni qayta tanlang.',
			}, status=409)
		if reservation.expires_at <= timezone.now():
			release_apartment_reservation(reservation)
			return JsonResponse({
				'success': False,
				'message': 'Kodning amal qilish muddati tugadi. Xonadonni qayta tanlang.',
			}, status=410)
		if not check_password(form.cleaned_data['code'], reservation.code_hash):
			reservation.attempts += 1
			if reservation.attempts >= 5:
				release_apartment_reservation(reservation)
			else:
				reservation.save(update_fields=['attempts'])
			return JsonResponse({
				'success': False,
				'message': 'Tasdiqlash kodi noto‘g‘ri. Kodni tekshirib qayta kiriting.',
			}, status=400)
		if reservation.apartment.availability != Apartment.Availability.RESERVED:
			release_apartment_reservation(reservation)
			return JsonResponse({
				'success': False,
				'message': 'Xonadonni bron qilib bo‘lmadi. Boshqa xonadon tanlang.',
			}, status=409)

		reservation.status = ApartmentReservation.Status.CONFIRMED
		reservation.confirmed_at = timezone.now()
		reservation.save(update_fields=['status', 'confirmed_at'])

	return JsonResponse({
		'success': True,
		'message': 'Email tasdiqlandi, xonadon broningiz muvaffaqiyatli tasdiqlandi.',
		'apartment_id': reservation.apartment_id,
	})


def contacts_view(request):
	return render(request, 'app/contacts.html', {
		'offices': SalesOffice.objects.all(),
	})


def partners_view(request):
	return render(request, 'app/partners.html')


def register_view(request):
	if request.user.is_authenticated:
		return redirect('home')
	if request.method == 'POST':
		form = UserRegisterForm(request.POST)
		if form.is_valid():
			user = form.save()
			auth_login(request, user)
			messages.success(request, 'Muvaffaqiyatli ro\'yxatdan o\'tdingiz!')
			return redirect('home')
	else:
		form = UserRegisterForm()
	return render(request, 'app/register.html', {'form': form})


def login_view(request):
	if request.user.is_authenticated:
		return redirect('home')
	if request.method == 'POST':
		form = UserLoginForm(request, data=request.POST)
		if form.is_valid():
			user = form.get_user()
			auth_login(request, user)
			messages.success(request, 'Xush kelibsiz!')
			return redirect('home')
	else:
		form = UserLoginForm()
	return render(request, 'app/login.html', {'form': form})


def logout_view(request):
	auth_logout(request)
	messages.info(request, 'Tizimdan chiqdingiz.')
	return redirect('home')


@login_required
def profile_view(request):
	profile_form = UserProfileForm(instance=request.user)
	password_form = OptionalPasswordChangeForm(request.user)

	if request.method == 'POST':
		profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user)
		password_submitted = any(key in request.POST for key in ('old_password', 'new_password1', 'new_password2'))
		password_form = OptionalPasswordChangeForm(request.user, request.POST) if password_submitted else OptionalPasswordChangeForm(request.user)

		profile_valid = profile_form.is_valid()
		password_valid = password_form.is_valid() if password_submitted else False

		if profile_valid:
			profile_form.save()
			messages.success(request, 'Profil ma`lumotlari saqlandi.')

		if password_valid:
			user = password_form.save()
			auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
			messages.success(request, 'Parolingiz muvaffaqiyatli yangilandi.')

		if profile_valid or password_valid:
			return redirect('profile')

	return render(request, 'app/profile.html', {
		'form': profile_form,
		'password_form': password_form,
	})


def send_password_reset_code_email(reset_code):
	subject = f"Xon Saroy — Parolni almashtirish kodi: {reset_code.code}"
	context = {
		'code': reset_code.code,
		'user': reset_code.user,
		'expires_minutes': 10,
	}
	html_content = render_to_string('emails/password_reset_code.html', context)
	text_content = (
		f"Assalomu alaykum, {reset_code.user.username}!\n\n"
		f"Xon Saroy hisobingiz parolini almashtirish uchun 6 xonali tasdiqlash kodi: {reset_code.code}\n\n"
		f"Ushbu kod 10 daqiqa davomida amal qiladi.\n"
		f"Agar parolni almashtirishni siz so'ramagan bo'lsangiz, ushbu xabarni e'tiborsiz qoldiring.\n\n"
		f"Hurmat bilan,\nXon Saroy"
	)
	from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
	if not from_email:
		host_user = getattr(settings, 'EMAIL_HOST_USER', '').strip()
		from_email = f"Xon Saroy <{host_user}>" if host_user else 'Xon Saroy <noreply@xonsaroy.uz>'

	email_msg = EmailMultiAlternatives(
		subject=subject,
		body=text_content,
		from_email=from_email,
		to=[reset_code.email],
	)
	email_msg.attach_alternative(html_content, 'text/html')
	return email_msg.send(fail_silently=False)


def send_password_reset_code_telegram(reset_code):
	chat_id = (
		getattr(reset_code.user, 'telegram_id', None)
		or os.getenv('TELEGRAM_ADMIN_CHAT_ID', '').strip()
	)
	if not chat_id:
		return False, 'Telegram chat ID topilmadi.'

	text = (
		'🔐 <b>Xon Saroy — Parolni tiklash kodi</b>\n\n'
		f'Assalomu alaykum, <b>{reset_code.user.username}</b>!\n'
		f'Hisobingiz (<code>{reset_code.email}</code>) parolini almashtirish uchun 6 xonali tasdiqlash kodingiz:\n\n'
		f'👉 <code>{reset_code.code}</code> 👈\n\n'
		'⏱ Ushbu kod <b>10 daqiqa</b> davomida amal qiladi.\n'
		'Agar siz ushbu amalni bajarmagan bo‘lsangiz, xabarga e’tibor bermang.'
	)
	return send_telegram_message(chat_id, text)


def password_reset_request_view(request):
	initial_email = ''
	if request.user.is_authenticated and request.user.email:
		initial_email = request.user.email
	elif request.GET.get('email'):
		initial_email = request.GET.get('email')

	if request.method == 'POST':
		form = PasswordResetRequestForm(request.POST)
		if form.is_valid():
			email = form.cleaned_data['email']
			user = User.objects.filter(email__iexact=email, is_active=True).first()
			if user:
				reset_code = PasswordResetCode.create_for_user(user, email=email)
				backend_name = str(getattr(settings, 'EMAIL_BACKEND', ''))
				is_live_smtp = 'smtp.EmailBackend' in backend_name
				email_sent = False
				send_err = None

				try:
					send_password_reset_code_email(reset_code)
					email_sent = True
				except Exception as e:
					send_err = str(e)

				tg_sent, _ = send_password_reset_code_telegram(reset_code)

				request.session['password_reset_email'] = email

				# Inform the user clearly where the code went
				if email_sent and is_live_smtp and tg_sent:
					messages.success(
						request,
						f"{email} pochtangizga va Telegramingizga 6 xonali tasdiqlash kodi yuborildi. Kod 10 daqiqa davomida amal qiladi."
					)
				elif tg_sent and not is_live_smtp:
					messages.success(
						request,
						f"Telegramingizga va pochtangizga 6 xonali tasdiqlash kodi yuborildi! Kod 10 daqiqa amal qiladi."
					)
				elif tg_sent:
					messages.success(
						request,
						f"Telegramingizga 6 xonali tasdiqlash kodi yuborildi! Kod 10 daqiqa amal qiladi."
					)
				elif email_sent and is_live_smtp:
					messages.success(
						request,
						f"{email} Gmail pochtangizga 6 xonali tasdiqlash kodi yuborildi. Kod 10 daqiqa davomida amal qiladi."
					)
				else:
					messages.success(
						request,
						f"{email} manziliga 6 xonali kod yuborildi (Kod: {reset_code.code}). Kod 10 daqiqa davomida amal qiladi."
					)

				return redirect('password_reset_confirm')
	else:
		form = PasswordResetRequestForm(initial={'email': initial_email})

	return render(request, 'app/password_reset_request.html', {
		'form': form,
	})


def password_reset_confirm_view(request):
	email = request.session.get('password_reset_email') or request.GET.get('email')
	if not email and request.user.is_authenticated and request.user.email:
		email = request.user.email

	if not email:
		messages.warning(request, 'Iltimos, avval elektron pochtangizni kiriting.')
		return redirect('password_reset_request')

	user = User.objects.filter(email__iexact=email, is_active=True).first()
	if not user:
		messages.error(request, 'Ushbu elektron pochtaga ega faol foydalanuvchi topilmadi.')
		return redirect('password_reset_request')

	latest_code = PasswordResetCode.objects.filter(user=user, is_used=False).order_by('-created_at').first()
	seconds_remaining = 0
	if latest_code and not latest_code.is_expired():
		seconds_remaining = max(0, int((latest_code.expires_at - timezone.now()).total_seconds()))

	if request.method == 'POST':
		form = PasswordResetConfirmForm(user, request.POST)
		if form.is_valid():
			new_password = form.cleaned_data['new_password1']
			user.set_password(new_password)
			user.save()

			form.reset_code_obj.is_used = True
			form.reset_code_obj.save(update_fields=['is_used'])

			if 'password_reset_email' in request.session:
				del request.session['password_reset_email']

			messages.success(request, 'Parolingiz muvaffaqiyatli almashtirildi! Yangi parol bilan tizimga kiring.')
			return redirect('login')
	else:
		form = PasswordResetConfirmForm(user)

	return render(request, 'app/password_reset_confirm.html', {
		'form': form,
		'email': email,
		'seconds_remaining': seconds_remaining,
	})


def password_reset_resend_view(request):
	email = request.session.get('password_reset_email') or request.GET.get('email')
	if not email and request.user.is_authenticated and request.user.email:
		email = request.user.email

	if not email:
		messages.error(request, 'Elektron pochta manzili topilmadi. Qaytadan boshlang.')
		return redirect('password_reset_request')

	user = User.objects.filter(email__iexact=email, is_active=True).first()
	if not user:
		messages.error(request, 'Foydalanuvchi topilmadi.')
		return redirect('password_reset_request')

	# Rate limiting: wait at least 30 seconds
	last_code = PasswordResetCode.objects.filter(user=user).order_by('-created_at').first()
	if last_code and (timezone.now() - last_code.created_at).total_seconds() < 30:
		remaining_wait = 30 - int((timezone.now() - last_code.created_at).total_seconds())
		messages.warning(request, f'Yangi kod yuborish uchun yana {remaining_wait} soniya kuting.')
		return redirect('password_reset_confirm')

	reset_code = PasswordResetCode.create_for_user(user, email=email)
	backend_name = str(getattr(settings, 'EMAIL_BACKEND', ''))
	is_live_smtp = 'smtp.EmailBackend' in backend_name
	email_sent = False
	send_err = None

	try:
		send_password_reset_code_email(reset_code)
		email_sent = True
	except Exception as e:
		send_err = str(e)

	tg_sent, _ = send_password_reset_code_telegram(reset_code)

	request.session['password_reset_email'] = email

	if email_sent and is_live_smtp and tg_sent:
		messages.success(request, 'Yangi 6 xonali tasdiqlash kodi emailingizga va Telegramingizga yuborildi (10 daqiqa amal qiladi).')
	elif tg_sent:
		messages.success(request, 'Yangi 6 xonali tasdiqlash kodi Telegramingizga yuborildi (10 daqiqa amal qiladi).')
	elif email_sent and is_live_smtp:
		messages.success(request, 'Yangi 6 xonali tasdiqlash kodi Gmail pochtangizga yuborildi (10 daqiqa amal qiladi).')
	else:
		messages.success(request, f'Yangi tasdiqlash kodi: {reset_code.code} (10 daqiqa amal qiladi).')

	return redirect('password_reset_confirm')


@require_GET
def apartment_detail_api(request, pk):
    """Return apartment details as JSON for the detail modal."""
    try:
        apartment = Apartment.objects.select_related('project', 'project__category').get(pk=pk, is_active=True)
    except Apartment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Xonadon topilmadi.'}, status=404)

    gallery = []
    # Add main plan image first
    if apartment.image_url:
        gallery.append({'url': apartment.image_url, 'caption': 'Xonadon rejasi'})
    elif apartment.image:
        gallery.append({'url': apartment.image.url, 'caption': 'Xonadon rejasi'})

    # Add gallery images
    for img in apartment.images.all():
        gallery.append({'url': img.image.url, 'caption': img.caption or ''})

    # Project info
    project_data = None
    if apartment.project:
        p = apartment.project
        project_data = {
            'name': p.name,
            'status': p.get_status_display(),
            'description': p.description or '',
            'image_url': p.image_url or (p.image.url if p.image else ''),
        }

    return JsonResponse({
        'success': True,
        'apartment': {
            'id': apartment.id,
            'rooms': apartment.rooms,
            'floor': apartment.floor,
            'area': str(apartment.area),
            'price': str(int(apartment.price)),
            'description': apartment.description or '',
            'gallery': gallery,
            'project': project_data,
        }
    })
