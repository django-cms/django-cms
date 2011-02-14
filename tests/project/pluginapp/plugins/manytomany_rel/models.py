from django.db import models

from cms.models import CMSPlugin

from project.pluginapp.models import Section


class ArticlePluginModel(CMSPlugin):
    title = models.CharField(max_length=50)
    sections =  models.ManyToManyField(Section)
    
    def __unicode__(self):
        return self.title
    
    def copy_relations(self, oldinstance):
        self.sections = oldinstance.sections.all()
