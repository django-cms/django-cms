from cms.utils.compat import PY2

if PY2:
    class UnittestCompatMixin(object):
        def assertNotRegex(self, text, regex, msg=None):
            return self.assertNotRegexpMatches(text, regex, msg)
else:
    class UnittestCompatMixin(object):
        pass