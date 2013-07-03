# -*- coding: utf-8 -*-
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

from models import Slideshow, SlideshowSlide


class SlideInline(admin.StackedInline):
    model = SlideshowSlide
    extra = 1
    

class SlideshowPlugin(CMSPluginBase):
    model = Slideshow
    name = _("Slideshow")
    render_template = "cms/plugins/slideshow/slideshow.html"
    
    inlines = [SlideInline]
    
    def render(self, context, instance, placeholder):
        context.update({
            'slideshow': instance,
            'placeholder': placeholder,
        })
        return context

plugin_pool.register_plugin(SlideshowPlugin)
