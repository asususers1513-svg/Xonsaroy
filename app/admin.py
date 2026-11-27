from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from .models import User, Category, Home, Apartment, ApartmentImage, ApartmentReservation, Material, Client, SalesOffice, PasswordResetCode, BotUser, Lead


@admin.register(User)
class UserAdmin(BaseUserAdmin):
	list_display = ('username', 'email', 'telegram_id', 'role', 'is_staff', 'is_active')
	list_filter = ('role', 'is_staff', 'is_active')
	fieldsets = BaseUserAdmin.fieldsets + (
		('Qo\'shimcha Ma\'lumotlar', {'fields': ('role', 'avatar', 'telegram_id')}),
	)
	add_fieldsets = BaseUserAdmin.add_fieldsets + (
		('Qo\'shimcha Ma\'lumotlar', {'fields': ('role', 'avatar', 'telegram_id')}),
	)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug')
	prepopulated_fields = {'slug': ('name',)}


@admin.register(Home)
class HomeAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'status', 'latitude', 'longitude', 'created_at')
	list_filter = ('status', 'category')
	list_editable = ('status',)
	search_fields = ('name', 'description')
	fields = ('name', 'category', 'image', 'hero_image', 'status', 'description', 'latitude', 'longitude')


class ApartmentImageInline(admin.TabularInline):
	model = ApartmentImage
	extra = 1
	fields = ('image', 'caption', 'sort_order')


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
	list_display = ('project', 'unit_number', 'rooms', 'floor', 'area', 'price', 'availability', 'is_active', 'sort_order')
	list_filter = ('project', 'rooms', 'floor', 'availability', 'is_active')
	list_editable = ('is_active', 'sort_order', 'price')
	fields = ('project', 'unit_number', 'rooms', 'floor', 'area', 'price', 'image', 'description', 'availability', 'is_active', 'sort_order')
	inlines = [ApartmentImageInline]


@admin.register(ApartmentReservation)
class ApartmentReservationAdmin(admin.ModelAdmin):
	list_display = ('apartment', 'name', 'email', 'phone', 'status', 'created_at', 'expires_at')
	list_filter = ('status', 'created_at')
	search_fields = ('name', 'email', 'phone', 'apartment__project__name')
	readonly_fields = ('public_id', 'apartment', 'name', 'email', 'phone', 'code_hash', 'attempts', 'created_at', 'expires_at', 'confirmed_at')
	list_editable = ('status',)
	actions = ('confirm_reservation', 'cancel_reservation')

	def save_model(self, request, obj, form, change):
		super().save_model(request, obj, form, change)
		obj.apartment.availability = (
			obj.apartment.Availability.RESERVED
			if obj.status in (obj.Status.PENDING, obj.Status.CONFIRMED)
			else obj.apartment.Availability.AVAILABLE
			if obj.status == obj.Status.EXPIRED
			else obj.apartment.availability
		)
		obj.apartment.save(update_fields=['availability'])

	@admin.action(description='Tanlangan bronni tasdiqlash')
	def confirm_reservation(self, request, queryset):
		now = timezone.now()
		updated = 0
		for reservation in queryset.select_related('apartment'):
			reservation.status = reservation.Status.CONFIRMED
			reservation.confirmed_at = now
			reservation.save(update_fields=['status', 'confirmed_at'])
			reservation.apartment.availability = reservation.apartment.Availability.RESERVED
			reservation.apartment.save(update_fields=['availability'])
			updated += 1
		self.message_user(request, f'{updated} ta bron tasdiqlandi.')

	@admin.action(description='Tanlangan bronni bekor qilish')
	def cancel_reservation(self, request, queryset):
		now = timezone.now()
		updated = 0
		for reservation in queryset.select_related('apartment'):
			reservation.status = reservation.Status.EXPIRED
			reservation.confirmed_at = None
			reservation.save(update_fields=['status', 'confirmed_at'])
			reservation.apartment.availability = reservation.apartment.Availability.AVAILABLE
			reservation.apartment.save(update_fields=['availability'])
			updated += 1
		self.message_user(request, f'{updated} ta bron bekor qilindi.')


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
	list_display = ('title', 'sort_order')
	list_editable = ('sort_order',)
	fields = ('title', 'image', 'video_url', 'sort_order')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
	list_display = ('name', 'sort_order')
	list_editable = ('sort_order',)
	fields = ('name', 'image', 'sort_order')


@admin.register(SalesOffice)
class SalesOfficeAdmin(admin.ModelAdmin):
	list_display = ('name', 'address', 'sort_order')
	list_editable = ('sort_order',)
	fields = ('name', 'address', 'latitude', 'longitude', 'sort_order')


@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
	list_display = ('user', 'email', 'code', 'created_at', 'expires_at', 'is_used', 'is_expired')
	list_filter = ('is_used', 'created_at')
	search_fields = ('email', 'code', 'user__username')
	readonly_fields = ('user', 'email', 'code', 'created_at', 'expires_at')


@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
	list_display = ('telegram_id', 'first_name', 'last_name', 'username', 'phone', 'language', 'last_activity')
	search_fields = ('telegram_id', 'first_name', 'last_name', 'username', 'phone')
	list_filter = ('language', 'created_at')
	readonly_fields = ('telegram_id', 'created_at', 'last_activity')


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
	list_display = ('name', 'phone', 'project', 'apartment', 'source', 'status', 'created_at')
	list_filter = ('status', 'source', 'project', 'created_at')
	list_editable = ('status',)
	search_fields = ('name', 'phone', 'telegram_username', 'note')
	readonly_fields = ('created_at',)
