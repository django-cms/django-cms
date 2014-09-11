from django.utils import six


if six.PY3:
    class UnittestCompatMixin(object):
        pass
else:
    class UnittestCompatMixin(object):
        def assertNotRegex(self, text, regex, msg=None):
            return self.assertNotRegexpMatches(text, regex, msg)
