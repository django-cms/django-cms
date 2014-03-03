from cms.utils.compat import PY2

if not PY2:
    string_types = (str, )
    int_types = (int, )
else:
    string_types = (str, unicode, )  # nopyflakes
    int_types = (int, long, )  # nopyflakes
