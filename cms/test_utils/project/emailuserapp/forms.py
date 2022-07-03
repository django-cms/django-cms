from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import EmailUser


class UserCreationForm(forms.ModelForm):
    """
    A form for creating a new user, including the required
    email and password fields.
    """

    error_messages = {
        'duplicate_email': "A user with that email already exists.",
        'password_mismatch': "The two password fields didn't match.",
    }

    email = forms.EmailField(
        label='Email',
        help_text="Required.  Standard format email address.",
    )

    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput
    )

    password2 = forms.CharField(
        label='Password confirmation',
        widget=forms.PasswordInput,
        help_text="Enter the same password as above, for verification."
    )

    class Meta:
        model = EmailUser
        fields = ('email',)

    def clean_email(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        email = self.cleaned_data["email"]

        User = get_user_model()

        try:
            User._default_manager.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(
            self.error_messages['duplicate_email'],
            code='duplicate_email',
        )

    def clean_password2(self):
        # check that the two passwords match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()

        return user


class UserChangeForm(forms.ModelForm):
    """
    A form for updating users, including all fields on the user,
    but replaces the password field with admin's password hash display
    field.
    """
    email = forms.EmailField(
        label='Email',
        help_text = "Required.  Standard format email address.",
    )

    password = ReadOnlyPasswordHashField(label="Password",
        help_text="Raw passwords are not stored, so there is no way to see "
                    "this user's password, but you can change the password "
                    "using <a href=\"password/\">this form</a>.")

    class Meta:
        model = EmailUser
        fields = ('email', 'password', 'first_name', 'last_name', 'is_active',
            'is_staff', 'is_superuser', 'groups', 'user_permissions', 'last_login',
            'date_joined')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        f = self.fields.get('user_permissions', None)
        if f is not None:
            f.queryset = f.queryset.select_related('content_type')

    def clean_password(self):
        """
        Regardless of what the user provides, return the initial value.
        This is done here, rather than on the field, because the
        field does not have access to the initial value.
        """
        return self.initial["password"]
