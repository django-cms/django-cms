# -*- coding: utf-8 -*-
import datetime

from django.utils.translation import get_language
from django.conf import settings


class LanguageCookieMiddleware(object):
    def process_response(self, request, response):
        language = get_language()
        if settings.LANGUAGE_COOKIE_NAME in request.COOKIES and \
                request.COOKIES[settings.LANGUAGE_COOKIE_NAME] == language:
            return response
        if not settings.SESSION_EXPIRE_AT_BROWSER_CLOSE:
            max_age = 365 * 24 * 60 * 60  # 10 years
            expires = datetime.datetime.now() + datetime.timedelta(seconds=max_age)
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language, expires=expires.utctimetuple(),
                                max_age=max_age)
        else:
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)
        return response

