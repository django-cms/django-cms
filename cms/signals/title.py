# -*- coding: utf-8 -*-


def pre_save_title(instance, raw, **kwargs):
    """Save old state to instance and setup path
    """
    if not instance.publisher_is_draft:
        return

    page = instance.page
    page_languages = page.get_languages()

    if not instance.language in page_languages:
        page_languages.append(instance.language)
        page.update_languages(page_languages)
