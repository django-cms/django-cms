# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.db import models

from django.core.exceptions import ValidationError
from cms.models import CMSPlugin


class Slideshow(CMSPlugin):
    name = models.CharField(verbose_name=_(u"name"), max_length=255)
    
    def get_slides(self):
        return self.slideshowslide_set.filter(active=True)
    
    def copy_relations(self, oldinstance):
        for slide in oldinstance.slideshowslide_set.all():
            new_slide = SlideshowSlide(
                slideshow = self,
                cms_page = slide.cms_page,
                url = slide.url,
                order = slide.order,
                caption = slide.caption,
                active = slide.active,
            )
            new_slide.save()
            if slide.image:
                new_slide.image.save(
                    slide.image.url.split('/')[-1],
                    slide.image.file,
                    save=True
                )

    class Meta:
        verbose_name = _("slideshow")
        verbose_name_plural = _("slideshows")

    def __unicode__(self):
        return "{} ({})".format(self.name, self.get_slides().count())


class SlideshowSlideManager(models.Manager):
    def get_queryset(self):
        return super(SlideshowSlideManager, self).get_queryset().filter(active=True)


class SlideshowSlide(models.Model):
    
    slideshow = models.ForeignKey(Slideshow)
    image = models.ImageField(
        _("image file"),
        upload_to=lambda slide,filename: slide.slideshow.get_media_path(filename),
        blank=True,
        width_field='image_width',
        height_field='image_height'
    )
    image_width  = models.IntegerField(null=True, blank=True, editable=False)
    image_height = models.IntegerField(null=True, blank=True, editable=False)
    cms_page = models.ForeignKey(
        'cms.Page',
        verbose_name=_(u"Link to another CMS page"), 
        blank=True, 
        null=True
    )
    url = models.URLField(verbose_name=_(u"URL"), blank=True, null=True)
    order = models.IntegerField(
        default=0,
        verbose_name=_(u"order"), 
        help_text=_("0=first, 1=second")
    )
    caption = models.TextField(
        verbose_name=_(u"caption"),
        blank=True,
    )
    active = models.BooleanField(
        verbose_name=_(u"enable slide"),
        default=True,
    )
    
    def clean(self):
        if not self.caption and not self.image:
            raise ValidationError(_(u"You have neither text nor image in this slide"))    
    
    class Meta:
        ordering = ["order"]
        verbose_name = _("slide image")
        verbose_name_plural = _("slide images")

    def __unicode__(self):
        return str(self.image)

