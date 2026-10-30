from django.conf import settings


def authentication_options(request):
    return {
        'google_oauth_enabled': settings.GOOGLE_OAUTH_ENABLED,
        'github_oauth_enabled': settings.GITHUB_OAUTH_ENABLED,
    }
