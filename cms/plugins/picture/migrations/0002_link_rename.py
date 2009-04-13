
from south.db import db
from django.db import models
from cms.plugins.picture.models import *

class Migration:
    
    def forwards(self, orm):
        db.rename_column('picture_picture', 'link', 'url')
    
    
    def backwards(self, orm):
        db.rename_column('picture_picture', 'url', 'link')
   