from urllib.parse import quote

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone


class EmailUserManager(BaseUserManager):

    def _create_user(self, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('Users are required to have an email address.')
        email = self.normalize_email(email)

        user = self.model(
            email=email,
            is_staff=is_staff, is_active=True,
            is_superuser=is_superuser, last_login=now,
            date_joined=now, **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email, password, **extra_fields):
        return self._create_user(email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        return self._create_user(email, password, True, True,
                                 **extra_fields)

class AbstractEmailUser(AbstractBaseUser, PermissionsMixin):
    """
    An abstract user model that is an alternative to the standard AbstractUser.  The
    sole difference is that AbstractEmailUser does not have a username field, and uses
    the email field as the primary identifier by default.

    Email and password are required. Other fields are optional.
    """

    email = models.EmailField(
        'email address',
        max_length=300,
        blank=True,
        unique=True,
        help_text = "Required.  Standard format email address."
    )

    first_name = models.CharField(
        'first name',
        max_length=30,
        blank=True
    )

    last_name = models.CharField(
        'last name',
        max_length=30,
        blank=True
    )

    is_staff = models.BooleanField(
        'staff status',
        default=False,
        help_text='Designates whether the user can log into this admin site.'
    )

    is_active = models.BooleanField(
        'active',
        default=True,
        help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'
    )

    date_joined = models.DateTimeField('date joined', default=timezone.now)

    objects = EmailUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        abstract = True

    def get_absolute_url(self):
        return "/users/%s/" % quote(self.pk)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])


class EmailUser(AbstractEmailUser):
    """
    Users within the Django authentication system are represented by this
    model.

    Email and password are required. Other fields are optional.
    """
