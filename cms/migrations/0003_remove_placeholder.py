# -*- coding: utf-8 -*-
from south.db import db
from django.db import models
from cms.models import *

class Migration:
    
    def forwards(self, orm):
        # Deleting model 'Placeholder'
        db.delete_table('cms_placeholder')
        
    
    def backwards(self, orm):
        
       # Adding model 'Placeholder'
        db.create_table('cms_placeholder', (
            ('body', models.TextField()),
            ('language', models.CharField(_("language"), db_index=True, max_length=3, editable=False, blank=False)),
            ('id', models.AutoField(primary_key=True)),
            ('name', models.CharField(_("slot"), max_length=50, editable=False, db_index=True)),
            ('page', models.ForeignKey(orm.Page, editable=False, verbose_name=_("page"))),
        ))
        db.send_create_signal('cms', ['Placeholder'])
        