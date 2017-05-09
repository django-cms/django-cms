from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, URLValidator

from cms.utils.urlutils import relative_url_regex


def validate_relative_url(value):
    RegexValidator(regex=relative_url_regex)(value)


def validate_url(value):
    try:
        # Validate relative urls first
        validate_relative_url(value)
    except ValidationError:
        # Fallback to absolute urls
        URLValidator()(value)
