"""Sample models for testing publisher
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from publisher import Publisher, Mptt


class Continent(models.Model):
    """Simple continent
    """
    name = models.CharField(max_length=32)
    
    class Meta:
        verbose_name=_('Continent')
        verbose_name_plural=_('Continents')
        
    # register for publisher
    # class Publisher(Publisher): pass        
    
    __unicode__ = lambda self: self.name

    
class Country(models.Model):
    """Simple country
    """
    name = models.CharField(max_length=64)
    population = models.PositiveIntegerField()
    continent = models.ForeignKey(Continent)
    
    class Meta:
        verbose_name=_('Country')
        verbose_name_plural=_('Countries')
        
        
    __unicode__ = lambda self: self.name


class Place(models.Model):
    """Simple place
    """
    name = models.CharField(max_length=128)
    country = models.ForeignKey(Country)
    description = models.TextField(max_length=1000)
    latitude = models.DecimalField(max_digits=10, decimal_places=4)
    longitude = models.DecimalField(max_digits=10, decimal_places=4)
    image = models.ImageField(upload_to='/uploads/place/%Y/%m/%d')
    
    class Meta:
        verbose_name=_('Place')
        verbose_name_plural=_('Places')
        
    __unicode__ = lambda self: 'change_me'
        
        
class Person(models.Model):
    """Simple person
    """
    user = models.ForeignKey(User)
    current_location = models.ForeignKey(Place)
    favorite_places = models.ManyToManyField(Place, related_name='person_likes_set')
    
    class Meta:
        verbose_name=_('Person')
        verbose_name_plural=_('Persons')
        
    # register for publisher
    #class Publisher(Publisher): pass
        
    __unicode__ = lambda self: unicode(self.user)

    
class Destination(models.Model):
    """Simple destination - test mptt
    """
    name = models.CharField(max_length=128, null=True, blank=True)
    place = models.ForeignKey(Place, null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    
    class Meta:
        verbose_name=_('Destination')
        verbose_name_plural=_('Destinations')
    
    # register for mptt
    class Mptt(Mptt): pass
    
    # register for publisher
    #class Publisher(Publisher): pass
    
    __unicode__ = lambda self: self.name or unicode(self.place)


# TODO: and what with inherited models..?

print "travel models()"