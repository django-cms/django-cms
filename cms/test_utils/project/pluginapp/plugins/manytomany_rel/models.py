from django.db import models

from cms.models import CMSPlugin


class Article(models.Model):
    title = models.CharField(max_length=50)
    section = models.ForeignKey('Section', on_delete=models.CASCADE)

    def __str__(self):
        return "%s -- %s" % (self.title, self.section)


class Section(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class ArticlePluginModel(CMSPlugin):
    title = models.CharField(max_length=50)
    sections = models.ManyToManyField('Section')

    def __str__(self):
        return self.title

    def copy_relations(self, oldinstance):
        self.sections.set(oldinstance.sections.all())


class FKModel(models.Model):
    fk_field = models.ForeignKey('PluginModelWithFKFromModel', on_delete=models.CASCADE)


class M2MTargetModel(models.Model):
    title = models.CharField(max_length=50)


class PluginModelWithFKFromModel(CMSPlugin):
    title = models.CharField(max_length=50)

    def copy_relations(self, oldinstance):
        # Like suggested in the docs
        for associated_item in oldinstance.fkmodel_set.all():
            associated_item.pk = None
            associated_item.fk_field = self
            associated_item.save()


class PluginModelWithM2MToModel(CMSPlugin):
    m2m_field = models.ManyToManyField(M2MTargetModel)

    def copy_relations(self, oldinstance):
        # Like suggested in the docs
        self.m2m_field.set(oldinstance.m2m_field.all())
