from dbgettext.registry import registry, Options
from models import Link

class LinkOptions(Options):
    attributes = ('name', 'url', 'mailto')
    parent = 'page'

registry.register(Link, LinkOptions)
