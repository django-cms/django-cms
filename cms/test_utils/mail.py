from django.core import mail

MAILERS_SUPPORTED = hasattr(mail, "mailers")
LOCMEM_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


def get_email_settings():
    """Configure in-memory email using the running Django's settings API."""
    if MAILERS_SUPPORTED:
        return {"MAILERS": {"default": {"BACKEND": LOCMEM_BACKEND}}}

    return {"EMAIL_BACKEND": LOCMEM_BACKEND}
