from django.conf import settings

default_modifiers = [
    'menus.modifiers.Marker',
    'menus.modifiers.Level',
    'menus.modifiers.LoginRequired',
]

def patch():
    if not hasattr(settings, 'MENU_MODIFIERS'):
        settings.MENU_MODIFIERS = default_modifiers