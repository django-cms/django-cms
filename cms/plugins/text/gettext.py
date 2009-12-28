from dbgettext.registry import registry, Options
from models import CMSPlugin
from dbgettext.parser import Token
from dbgettext.lexicons import html
from models import Text
import re

class PluginToken(Token):
    """ A CMSPlugin placeholder """

    def __init__(self, raw, obj):
        super(PluginToken, self).__init__('plugin', raw)
        self.obj = obj

    def is_translatable(self):
        return Token.ALWAYS_TRANSLATE

    def get_key(self):
        obj, cls = self.obj.get_plugin_instance()
        return '%s-%d:%s' % (repr(cls), obj.id, re.sub('\W', '_', str(obj)))


class TextOptions(Options):
    parsed_attributes = {'body': html.lexicon}
    parent = 'page'

    from cms.plugins.text.utils import OBJ_ADMIN_RE_PATTERN

    def plugin(scanner, token):
        try:
            obj = CMSPlugin.objects.get(pk=scanner.match.groups()[0])
        except CMSPlugin.DoesNotExist:
            obj = None
        return PluginToken(token, obj)

    custom_lexicon_rules = [(OBJ_ADMIN_RE_PATTERN, plugin),]


registry.register(Text, TextOptions)
