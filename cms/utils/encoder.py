from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_str
from django.utils.functional import Promise
from django.utils.html import conditional_escape


class SafeJSONEncoder(DjangoJSONEncoder):
    def _recursive_escape(self, o, esc=conditional_escape):
        if isinstance(o, dict):
            return type(o)((esc(k), self._recursive_escape(v)) for (k, v) in o.items())
        if isinstance(o, (list, tuple)):
            return type(o)(self._recursive_escape(v) for v in o)
        if type(o) is bool:
            return o
        try:
            return type(o)(esc(o))
        except (ValueError, TypeError):
            return self.default(o)

    def encode(self, o):
        value = self._recursive_escape(o)
        return super().encode(value)

    def default(self, o):
        if isinstance(o, Promise):
            return force_str(o)
        return super().default(o)
