from dbgettext.registry import registry, Options
from models import Picture

class PictureOptions(Options):
    attributes = ('url', 'alt')
    parent = 'page'

registry.register(Picture, PictureOptions)
