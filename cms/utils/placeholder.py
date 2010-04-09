from cms.models.pagemodel import Page

def get_page_from_placeholder_if_exists(placeholder):
    try:
        return Page.objects.get(placeholders=placeholder)
    except Page.DoesNotExist:
        return None