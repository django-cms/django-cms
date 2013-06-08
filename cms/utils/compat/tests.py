from cms.utils.compat import PY2

if PY2:
    class UnittestCompatMixin(object):
        def assertListEqual(self, a, b, msg=None):
            return self.assertItemsEqual(a, b, msg)

        def assertNotRegex(self, text, regex, msg=None):
            return self.assertNotRegexpMatches(text, regex, msg)
else:
    class UnittestCompatMixin(object):
        pass