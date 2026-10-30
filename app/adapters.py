import logging
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

logger = logging.getLogger(__name__)

class DebugSocialAccountAdapter(DefaultSocialAccountAdapter):
    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        print(f"\n==================== ALLAUTH AUTHENTICATION ERROR ====================")
        print(f"Provider: {provider}")
        print(f"Error: {error}")
        print(f"Exception: {repr(exception)}")
        if hasattr(exception, 'response') and exception.response is not None:
            try:
                print(f"Exception Response Status: {exception.response.status_code}")
                print(f"Exception Response Body: {exception.response.text}")
            except Exception as e:
                print(f"Could not read response: {e}")
        print(f"=======================================================================\n")
        super().on_authentication_error(request, provider, error, exception, extra_context)
