from django.core import mail as django_mail

LOCMEM_EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


def get_locmem_email_settings():
    """Return locmem backend settings using the API supported by this Django version."""
    if hasattr(django_mail, "mailers"):
        return {
            "MAILERS": {
                "default": {
                    "BACKEND": LOCMEM_EMAIL_BACKEND,
                },
            },
        }
    return {"EMAIL_BACKEND": LOCMEM_EMAIL_BACKEND}
