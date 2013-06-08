from cms.utils.compat.dj import python_2_unicode_compatible
from django.db import models


@python_2_unicode_compatible
class Section(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Article(models.Model):
    title = models.CharField(max_length=50)
    section = models.ForeignKey(Section)
    
    def __str__(self):
        return u"%s -- %s" % (self.title, self.section) 
