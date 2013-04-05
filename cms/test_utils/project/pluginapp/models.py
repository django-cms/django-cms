from django.db import models


class Section(models.Model):
    name = models.CharField(max_length=50)
    
    def __unicode__(self):
        return self.name

class Article(models.Model):
    title = models.CharField(max_length=50)
    section = models.ForeignKey(Section)
    
    def __unicode__(self):
        return u"%s -- %s" % (self.title, self.section) 
