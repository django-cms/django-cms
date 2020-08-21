from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    pass


class LoginForm2(AuthenticationForm):
    pass


class LoginForm3(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
