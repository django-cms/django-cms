from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import get_language

from cms.utils.compat import DJANGO_2_2

if DJANGO_2_2:
    from django.utils.translation import LANGUAGE_SESSION_KEY


class LanguageCookieMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)

    if DJANGO_2_2:

        def __call__(self, request):
            response = self.get_response(request)
            language = get_language()
            if hasattr(request, 'session'):
                session_language = request.session.get(LANGUAGE_SESSION_KEY, None)
                if session_language and not session_language == language:
                    request.session[LANGUAGE_SESSION_KEY] = language
                    request.session.save()
            if (
                settings.LANGUAGE_COOKIE_NAME in request.COOKIES
                and request.COOKIES[settings.LANGUAGE_COOKIE_NAME] == language  # noqa: W503
            ):
                return response
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                value=language,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                max_age=settings.LANGUAGE_COOKIE_AGE or 365 * 24 * 60 * 60,  # 1 year
                path=settings.LANGUAGE_COOKIE_PATH,
            )
            return response
    else:

        def __call__(self, request):
            response = self.get_response(request)
            language = get_language()
            if (
                settings.LANGUAGE_COOKIE_NAME in request.COOKIES  # noqa: W503
                and request.COOKIES[settings.LANGUAGE_COOKIE_NAME] == language
            ):
                return response

            # To ensure support of very old browsers, Django processed automatically "expires" according
            # to max_age value.
            # https://docs.djangoproject.com/en/3.2/ref/request-response/#django.http.HttpResponse.set_cookie

            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                value=language,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                max_age=settings.LANGUAGE_COOKIE_AGE or 365 * 24 * 60 * 60,  # 1 year
                httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                path=settings.LANGUAGE_COOKIE_PATH,
                samesite=settings.LANGUAGE_COOKIE_SAMESITE,
                secure=settings.LANGUAGE_COOKIE_SECURE,
            )
            return response
