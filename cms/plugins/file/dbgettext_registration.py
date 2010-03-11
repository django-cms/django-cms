from dbgettext.registry import registry, Options
from models import File

class FileOptions(Options):
    attributes = ('title',)
    parent = 'page'

registry.register(File, FileOptions)
