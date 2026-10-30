from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Category, Home, Apartment, ApartmentImage, Material, Client, SalesOffice, PasswordResetCode, BotUser, Lead


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
	list_display = ('name', 'category', 'status', 'created_at')
	list_filter = ('status', 'category')
	list_editable = ('status',)
	search_fields = ('name', 'description')
	fields = ('name', 'category', 'image', 'hero_image', 'status', 'description')


class ApartmentImageInline(admin.TabularInline):
	model = ApartmentImage
	extra = 1
	fields = ('image', 'caption', 'sort_order')


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
	list_display = ('project', 'rooms', 'floor', 'area', 'price', 'is_active', 'sort_order')
	list_filter = ('project', 'rooms', 'floor', 'is_active')
	list_editable = ('is_active', 'sort_order', 'price')
	fields = ('project', 'rooms', 'floor', 'area', 'price', 'image', 'description', 'is_active', 'sort_order')
	inlines = [ApartmentImageInline]


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
