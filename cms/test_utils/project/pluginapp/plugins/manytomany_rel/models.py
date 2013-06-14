from cms.utils.compat.dj import python_2_unicode_compatible
from django.db import models

from cms.models import CMSPlugin

from cms.test_utils.project.pluginapp.models import Section


@python_2_unicode_compatible
class ArticlePluginModel(CMSPlugin):
    title = models.CharField(max_length=50)
    sections =  models.ManyToManyField(Section)
    
    def __str__(self):
        return self.title
    
    def copy_relations(self, oldinstance):
        self.sections = oldinstance.sections.all()
