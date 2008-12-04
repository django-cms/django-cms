from datetime import datetime

from django.db import models

class Version(models.Model):
    signature = models.TextField()
    when = models.DateTimeField(default=datetime.now)

    class Meta:
        ordering = ('-when',)
        db_table = 'django_project_version'

    def __unicode__(self):
        if not self.evolutions.count():
            return u'Hinted version, updated on %s' % self.when
        return u'Stored version, updated on %s' % self.when

class Evolution(models.Model):
    version = models.ForeignKey(Version, related_name='evolutions')
    app_label = models.CharField(max_length=200)
    label = models.CharField(max_length=100)

    class Meta:
        db_table = 'django_evolution'
        
    def __unicode__(self):
        return u"Evolution %s, applied to %s" % (self.label, self.app_label)
