import secrets
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.text import slugify


class User(AbstractUser):
	class Role(models.TextChoices):
		ADMIN = 'admin', 'Admin'
		MODERATOR = 'moderator', 'Moderator'
		ORDINARY_USER = 'ordinary_user', 'Oddiy foydalanuvchi'

	role = models.CharField(
		max_length=20,
		choices=Role.choices,
		default=Role.ORDINARY_USER,
		verbose_name='Roli'
	)
	avatar = models.ImageField(
		upload_to='avatars/',
		blank=True,
		null=True,
		verbose_name='Avatar'
	)
	telegram_id = models.CharField(
		max_length=64,
		blank=True,
		null=True,
		verbose_name='Telegram ID'
	)

	def __str__(self):
		return f"{self.username} ({self.get_role_display()})"


class Category(models.Model):
	name = models.CharField(max_length=120, verbose_name='Kategoriya nomi')
	slug = models.SlugField(unique=True, blank=True)

	class Meta:
		verbose_name = 'Kategoriya'
		verbose_name_plural = 'Kategoriyalar'
		ordering = ('name',)

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name


class Home(models.Model):
	class Status(models.TextChoices):
		SOON = 'soon', 'Tez kunda'
		IN_PROGRESS = 'in_progress', 'Jarayonda'
		COMPLETED = 'completed', 'Yakunlangan'

	name = models.CharField(max_length=120)
	category = models.ForeignKey(
		Category,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='homes',
		verbose_name='Kategoriya'
	)
	image = models.ImageField(upload_to='projects/', blank=True, verbose_name='Loyiha rasmi')
	image_url = models.URLField(blank=True, editable=False)
	hero_image = models.ImageField(upload_to='projects/hero/', blank=True, verbose_name='Banner rasmi')
	hero_image_url = models.URLField(blank=True, editable=False)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
	description = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ('-created_at', 'name')

	def __str__(self):
		return self.name


class Apartment(models.Model):
	project = models.ForeignKey(Home, on_delete=models.SET_NULL, related_name='apartments', null=True, blank=True)
	rooms = models.PositiveSmallIntegerField(default=1, verbose_name='Xonalar soni')
	floor = models.PositiveSmallIntegerField(verbose_name='Qavat')
	area = models.DecimalField(max_digits=6, decimal_places=1, verbose_name='Maydon (m²)')
	price = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name='Narx (so\'m)')
	image = models.ImageField(upload_to='apartments/plans/', blank=True, verbose_name='Xonadon rejasi')
	image_url = models.URLField(blank=True, editable=False)
	description = models.TextField(blank=True, verbose_name='Tavsif')
	is_active = models.BooleanField(default=True, verbose_name='Faol')
	sort_order = models.PositiveSmallIntegerField(default=0, verbose_name='Tartib raqami')

	class Meta:
		ordering = ('sort_order', 'id')

	def __str__(self):
		return f'{self.project} — {self.rooms} xonali, {self.area} m², {self.price:,.0f} so\'m'


class ApartmentImage(models.Model):
	apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='images', verbose_name='Xonadon')
	image = models.ImageField(upload_to='apartments/gallery/', verbose_name='Rasm')
	caption = models.CharField(max_length=200, blank=True, verbose_name='Rasm tavsifi')
	sort_order = models.PositiveSmallIntegerField(default=0, verbose_name='Tartib raqami')

	class Meta:
		ordering = ('sort_order', 'id')
		verbose_name = 'Xonadon rasmi'
		verbose_name_plural = 'Xonadon rasmlari'

	def __str__(self):
		return f'{self.apartment} — rasm #{self.sort_order}'


class Material(models.Model):
	title = models.CharField(max_length=200, verbose_name='Material nomi')
	image = models.ImageField(upload_to='materials/', blank=True, verbose_name='Material rasmi')
	image_url = models.URLField(blank=True, editable=False)
	video_url = models.URLField(blank=True, verbose_name='Video havolasi')
	sort_order = models.PositiveSmallIntegerField(default=0, verbose_name='Tartib raqami')

	class Meta:
		ordering = ('sort_order', 'id')

	def __str__(self):
		return self.title


class Client(models.Model):
	name = models.CharField(max_length=120, verbose_name='Mijoz ismi')
	image = models.ImageField(upload_to='clients/', blank=True, verbose_name='Mijoz rasmi')
	image_url = models.URLField(blank=True, editable=False)
	sort_order = models.PositiveSmallIntegerField(default=0, verbose_name='Tartib raqami')

	class Meta:
		ordering = ('sort_order', 'id')

	def __str__(self):
		return self.name


class SalesOffice(models.Model):
	name = models.CharField(max_length=120, verbose_name='Ofis nomi')
	address = models.CharField(max_length=240, verbose_name='Manzil')
	latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Kenglik')
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Uzunlik')
	sort_order = models.PositiveSmallIntegerField(default=0, verbose_name='Tartib raqami')

	class Meta:
		ordering = ('sort_order', 'id')

	def __str__(self):
		return self.name


class PasswordResetCode(models.Model):
	user = models.ForeignKey(
		'app.User',
		on_delete=models.CASCADE,
		related_name='password_reset_codes',
		verbose_name='Foydalanuvchi'
	)
	email = models.EmailField(verbose_name='Elektron pochta')
	code = models.CharField(max_length=6, verbose_name='6 xonali kod')
	created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqt')
	expires_at = models.DateTimeField(verbose_name='Amal qilish muddati')
	is_used = models.BooleanField(default=False, verbose_name='Ishlatilgan')

	class Meta:
		verbose_name = 'Parolni tiklash kodi'
		verbose_name_plural = 'Parolni tiklash kodlari'
		ordering = ('-created_at',)

	def __str__(self):
		return f"{self.email} - {self.code} ({'Ishlatilgan' if self.is_used else 'Faol'})"

	@classmethod
	def create_for_user(cls, user, email=None):
		target_email = email or user.email
		cls.objects.filter(user=user, is_used=False).update(is_used=True)
		code = f"{secrets.randbelow(900000) + 100000}"
		now = timezone.now()
		expires_at = now + timedelta(minutes=10)
		return cls.objects.create(
			user=user,
			email=target_email,
			code=code,
			expires_at=expires_at,
			is_used=False
		)

	def is_expired(self):
		return timezone.now() > self.expires_at

	def is_valid(self):
		return (not self.is_used) and (not self.is_expired())


class BotUser(models.Model):
	telegram_id = models.CharField(max_length=64, unique=True, verbose_name='Telegram ID')
	first_name = models.CharField(max_length=120, blank=True, verbose_name='Ism')
	last_name = models.CharField(max_length=120, blank=True, verbose_name='Familiya')
	username = models.CharField(max_length=120, blank=True, null=True, verbose_name='Username')
	phone = models.CharField(max_length=30, blank=True, null=True, verbose_name='Telefon')
	language = models.CharField(max_length=5, default='uz', verbose_name='Tanlangan til')
	created_at = models.DateTimeField(auto_now_add=True, verbose_name='Qo‘shilgan vaqt')
	last_activity = models.DateTimeField(auto_now=True, verbose_name='Oxirgi faollik')

	class Meta:
		verbose_name = 'Bot foydalanuvchisi'
		verbose_name_plural = 'Bot foydalanuvchilari'
		ordering = ('-last_activity',)

	def __str__(self):
		return f"{self.first_name} ({self.telegram_id}) - {self.language}"


class Lead(models.Model):
	class Source(models.TextChoices):
		TELEGRAM = 'telegram', 'Telegram Bot'
		WEBSITE = 'website', 'Veb-sayt'

	class Status(models.TextChoices):
		NEW = 'new', 'Yangi'
		IN_CONTACT = 'in_contact', 'Bog‘lanildi'
		CLOSED = 'closed', 'Yakunlandi'

	name = models.CharField(max_length=120, verbose_name='Ism')
	phone = models.CharField(max_length=30, verbose_name='Telefon')
	telegram_id = models.CharField(max_length=64, blank=True, null=True, verbose_name='Telegram ID')
	telegram_username = models.CharField(max_length=120, blank=True, null=True, verbose_name='Telegram username')
	source = models.CharField(max_length=20, choices=Source.choices, default=Source.TELEGRAM, verbose_name='Manba')
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, verbose_name='Holati')
	project = models.ForeignKey(Home, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads', verbose_name='Qiziqqan loyihasi')
	apartment = models.ForeignKey(Apartment, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads', verbose_name='Qiziqqan xonadoni')
	note = models.TextField(blank=True, verbose_name='Qo‘shimcha ma’lumot / Xabar')
	created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yuborilgan vaqt')

	class Meta:
		verbose_name = 'Ariza (Lead)'
		verbose_name_plural = 'Arizalar (Leads)'
		ordering = ('-created_at',)

	def __str__(self):
		return f"{self.name} - {self.phone} ({self.get_source_display()})"
