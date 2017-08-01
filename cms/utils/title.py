# -*- coding: utf-8 -*-
from cms.models import Title


def has_redirect_loop(title, language, redirect_path):
    redirect_path = redirect_path.strip('/')
    try:
        redirected_titles = Title.objects.filter(language=language, path=redirect_path)
    except Title.DoesNotExist:
        return False
    if title.pk in redirected_titles.values_list('pk', flat=True):
        return True
    else:
        for redirected_title in redirected_titles:
            if redirected_title.redirect:
                if has_redirect_loop(title, language, redirected_title.redirect):
                    return True
        return False
