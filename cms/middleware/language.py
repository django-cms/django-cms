# -*- coding: utf-8 -*-
import datetime

from django.utils.translation import LANGUAGE_SESSION_KEY, get_language
from django.conf import settings


class LanguageCookieMiddleware(object):
    def process_response(self, request, response):
        language = get_language()
        if hasattr(request, 'session'):
            session_language = request.session.get(LANGUAGE_SESSION_KEY, None)
            if session_language and not session_language == language:
                request.session[LANGUAGE_SESSION_KEY] = language
                request.session.save()
        if settings.LANGUAGE_COOKIE_NAME in request.COOKIES and \
                        request.COOKIES[settings.LANGUAGE_COOKIE_NAME] == language:
            return response
        max_age = 365 * 24 * 60 * 60  # 10 years
        expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age)
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language, expires=expires)
        return response
