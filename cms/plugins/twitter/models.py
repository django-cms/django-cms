from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models.pluginmodel import CMSPlugin

class TwitterRecentEntries(CMSPlugin):
    title = models.CharField(_('title'), max_length=75, blank=True)
    twitter_user = models.CharField(_('twitter user'), max_length=75)
    count = models.PositiveSmallIntegerField(_('count'), help_text=_('Number of entries to display'), default=3)
    link_hint = models.CharField(_('link hint'), max_length=75, blank=True, help_text=_('If given, the hint is displayed as link to your Twitter profile.'))
    
    def __unicode__(self):
        return self.title

class TwitterSearch(CMSPlugin):
    title = models.CharField(_('title'), max_length=75, blank=True)
    query = models.CharField(_('query'), max_length=200, blank=True, default='', help_text=_('Example: "brains AND zombies AND from:umbrella AND to:nemesis": tweets from the user "umbrella" to the user "nemesis" that contain the words "brains" and "zombies"'))
    count = models.PositiveSmallIntegerField(_('count'), help_text=_('Number of entries to display'), default=3)
    
    def __unicode__(self):
        return self.title