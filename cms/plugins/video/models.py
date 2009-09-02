import re
from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin
from os.path import basename

class Video(CMSPlugin):
    CLICK_TARGET_BLANK = '_blank'
    CLICK_TARGET_SELF = '_self'
    CLICK_TARGET_PARENT = '_parent'
    
    WMODE_WINDOW = 'window'
    WMODE_OPAQUE = 'opaque'
    WMODE_TRANSPARENT = 'transparent'
    
    click_target_choices = (
        (CLICK_TARGET_BLANK, _('blank')),
        (CLICK_TARGET_SELF, _('self')),
        (CLICK_TARGET_PARENT, _('parent')),
    )
    
    wmode_choices = (
        (WMODE_WINDOW, _('window')),
        (WMODE_OPAQUE, _('opaque')),
        (WMODE_TRANSPARENT, _('transparent')),
    )
    # player settings
    movie = models.FileField(_('movie'), upload_to=CMSPlugin.get_media_path, help_text=_('use swf file'))
    image = models.ImageField(_('image'), upload_to=CMSPlugin.get_media_path, help_text=_('use image file'), null=True, blank=True)
    
    width = models.CharField(_('width'), max_length=6)
    height = models.CharField(_('height'), max_length=6)
    
    auto_load = models.BooleanField(_('auto load'), default=True)
    auto_play = models.BooleanField(_('auto play'), default=False)
    loop = models.BooleanField(_('loop'), default=False)
    volume = models.SmallIntegerField(_('volume'), default=50, help_text=_('in range <0, 100>'))
    
    click_url = models.URLField(_('click_url'), blank=True, null=True)
    click_target = models.CharField(_('click target'), max_length=7, choices=click_target_choices, default=CLICK_TARGET_BLANK)
    
    # plugin settings
    bgcolor = models.CharField(_('bgcolor'), max_length=6, default="000000", help_text=_('Hexadecimal, eg fff000'))
    fullscreen = models.BooleanField(_('fullscreen'), default=False)
    wmode = models.CharField(_('wmode'), max_length=10, choices=wmode_choices, default=WMODE_OPAQUE)
    flash_menu = models.BooleanField(_('flash menu'), default=False)
    
    
    def get_height(self):
        return fix_unit(self.height)
    
    def get_width(self):
        return fix_unit(self.width)    
        
    def __unicode__(self):
        return u"%s" % basename(self.movie.path)


def fix_unit(value):
    if not re.match(r'.*[0-9]$', value):
        # no unit, add px
        return value + "px"
    return value 
