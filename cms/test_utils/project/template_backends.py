from django.template.backends.django import DjangoTemplates


class CustomDjangoTemplates(DjangoTemplates):
    """
    A custom template engine that inherits from DjangoTemplates
    """

    pass


class NonDjangoTemplates:
    """
    A mock template backend that doesn't inherit from DjangoTemplates
    """

    def __init__(self, params):
        self.params = params
        self.engine = None

    def get_template(self, template_name):
        pass
