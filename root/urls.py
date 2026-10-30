from pathlib import Path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from app.views import (
    home, login_view, register_view, logout_view, profile_view, contact_submit,
    contacts_view, partners_view,
    password_reset_request_view, password_reset_confirm_view, password_reset_resend_view,
    apartment_detail_api,
)

urlpatterns = [
    path('', home, name='home'),
    path('contacts/', contacts_view, name='contacts'),
    path('partners/', partners_view, name='partners'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('contact/submit/', contact_submit, name='contact_submit'),
    path('password-reset/', password_reset_request_view, name='password_reset_request'),
    path('password-reset/verify/', password_reset_confirm_view, name='password_reset_confirm'),
    path('password-reset/resend/', password_reset_resend_view, name='password_reset_resend'),
    path('accounts/password/reset/', password_reset_request_view, name='account_reset_password'),
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)