# -*- coding: utf-8 -*-
from cms.models.cmsmodel import CMSModelBase
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _
from djangocms_text_ckeditor.fields import HTMLField
from cms.models.fields import PlaceholderField


@python_2_unicode_compatible
class Publisher(CMSModelBase):
    name = models.CharField(max_length=30)
    slug = models.SlugField(max_length=30)
    is_active = models.BooleanField(default=True,
            help_text='published on the web site', )
    address = models.CharField(max_length=50)
    city = models.CharField(max_length=60)
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=50)
    website = models.URLField()
    presentation = HTMLField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        cms_add_to_cms_toolbar = True

@python_2_unicode_compatible
class Author(CMSModelBase):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=40)
    is_active = models.BooleanField(default=True,
            help_text='published on the web site', )
    email = models.EmailField()
    is_alive = models.BooleanField(default=True)

    def __str__(self):
        return '%s %s' % (self.first_name.title(), self.last_name.upper())

    class Meta:
        ordering = ['last_name', 'first_name']
        cms_add_to_cms_toolbar = True

@python_2_unicode_compatible
class Ressource(CMSModelBase):
    LANGUAGE_ENGLISH = 'eng'
    LANGUAGE_FRENCH = 'fre'
    LANGUAGE_SINDARIN = 'srj'
    LANGUAGE_CHOICES = (
        (LANGUAGE_ENGLISH, _('English')),
        (LANGUAGE_FRENCH, _('French')),
        (LANGUAGE_SINDARIN, _('Sindarin')),
    )
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    is_active = models.BooleanField(default=True,
        help_text='published on the web site', )
    authors = models.ManyToManyField(Author)
    publisher = models.ForeignKey(Publisher)
    publication_date = models.DateField()
    still_published = models.BooleanField(default=True)
    public_domain = models.BooleanField(default=False)
    language = models.CharField(default=LANGUAGE_ENGLISH,
        max_length=3, choices=LANGUAGE_CHOICES,)
    summary = HTMLField()
    description = PlaceholderField('book_description')

    class Meta:
        abstract = True

    def __str__(self):
        return self.title.title()


class Book(Ressource):
    nb_pages = models.PositiveSmallIntegerField()
    
    class Meta:
        ordering = ['-publication_date',]
        cms_add_to_cms_toolbar = True


class PublicBookProxy(Book):
    class Meta:
        proxy = True
        cms_add_to_cms_toolbar = False
        verbose_name = 'Book in public domain'
        verbose_name_plural = 'Books in public domain'


class DVD(Ressource):
    duration = models.PositiveSmallIntegerField(help_text='in minutes')
    
    class Meta:
        ordering = ['-publication_date',]
        cms_add_to_cms_toolbar = True
        cms_create_admin_model = True
        cms_create_app = True
        cms_create_plugin = True
        cms_detail_view = True
