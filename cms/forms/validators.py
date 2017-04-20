from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, URLValidator

from cms.utils.urlutils import relative_url_regex


def validate_url(value):
    try:
        # Validate relative urls first
        RegexValidator(regex=relative_url_regex)(value)
    except ValidationError:
        # Fallback to absolute urls
        URLValidator()(value)
