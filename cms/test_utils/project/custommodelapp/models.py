from cms.models.cmsmodel import CMSModelBase
from django.db import models
from djangocms_text_ckeditor.fields import HTMLField
from cms.models.fields import PlaceholderField


class Publisher(CMSModelBase):
    name = models.CharField(max_length=30)
    slug = models.SlugField(max_length=30)
    published = models.BooleanField()
    address = models.CharField(max_length=50)
    city = models.CharField(max_length=60)
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=50)
    website = models.URLField()
    presentation = HTMLField()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']
        cms_add_to_cms_toolbar = True

class Author(CMSModelBase):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=40)
    published = models.BooleanField()
    email = models.EmailField()
    is_alive = models.BooleanField()

    def __unicode__(self):
        return u'%s %s' % (self.first_name.title(), self.last_name.upper())

    class Meta:
        ordering = ['last_name', 'first_name']
        cms_add_to_cms_toolbar = True
        cms_create_admin_model = False
        cms_create_app = False
    
class Book(CMSModelBase):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    published = models.BooleanField()
    authors = models.ManyToManyField(Author)
    publisher = models.ForeignKey(Publisher)
    publication_date = models.DateField()
    still_published = models.DateField()
    public_domain = models.DateField()
    summary = HTMLField()
    description = PlaceholderField('book_description')
    
    def __unicode__(self):
        return self.title.title()
    
    class Meta:
        ordering = ['-publication_date',]
        cms_add_to_cms_toolbar = True
