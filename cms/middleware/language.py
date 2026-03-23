from django.conf import settings
from django.utils.translation import get_language


class LanguageCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__()

    def __call__(self, request):
        response = self.get_response(request)
        return self.process_response(request, response)

    async def __acall__(self, request):
        response = await self.get_response(request)
        return self.process_response(request, response)

    def process_response(self, request, response):
        language = get_language()
        if (
            settings.LANGUAGE_COOKIE_NAME in request.COOKIES
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
