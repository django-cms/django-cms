"""Sample models for testing publisher
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from publisher.models import Publisher, Mptt

class Continent(Publisher):
    """Simple continent
    
    >>> hasattr(Continent, 'Public')
    True
    
    >>> continent = Continent(name="Europe")
    >>> continent.save()
    
    >>> pub_continent = Continent.Public(name="Public Europe", origin=continent)
    >>> pub_continent.save()
    
    >>> Continent.objects.count()
    1
    >>> Continent.Public.objects.count()
    1
    
    >>> pub_continent == Continent.objects.get(pk=continent.id).public
    True
    
    """
    name = models.CharField(max_length=32)
    
    class Meta:
        verbose_name=_('Continent')
        verbose_name_plural=_('Continents')
        
        
    __unicode__ = lambda self: self.name

class Country(models.Model):
    """Simple country
    
    >>> hasattr(Country, 'Public')
    False
    """
    name = models.CharField(max_length=64)
    population = models.PositiveIntegerField()
    continent = models.ForeignKey(Continent)
    
    class Meta:
        verbose_name=_('Country')
        verbose_name_plural=_('Countries')
        
    __unicode__ = lambda self: self.name


class Place(Publisher):
    """Simple place
    
    >>> hasattr(Place, 'Public')
    True
    """
    name = models.CharField(max_length=128)
    country = models.ForeignKey(Country)
    description = models.TextField(max_length=1000, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=4)
    longitude = models.DecimalField(max_digits=10, decimal_places=4)
    image = models.ImageField(upload_to='/uploads/place/%Y/%m/%d', null=True, blank=True)
    
    class Meta:
        verbose_name=_('Place')
        verbose_name_plural=_('Places')
        
    __unicode__ = lambda self: self.name
        
        
class Person(Publisher):
    """Simple person
    
    >>> hasattr(Person, 'Public')
    True
    >>> hasattr(User, 'Public')
    False
    
    """
    user = models.ForeignKey(User)
    current_location = models.ForeignKey(Place)
    favorite_places = models.ManyToManyField(Place, related_name='person_likes_set')
    
    class Meta:
        verbose_name=_('Person')
        verbose_name_plural=_('Persons')
        
    __unicode__ = lambda self: unicode(self.user)

    
class Destination(Publisher, Mptt):
    """Simple destination - test mptt
    
    >>> hasattr(Destination, 'Public')
    True
    
    >>> continent = Continent(name="Europe")
    >>> continent.save()
    
    >>> country = Country(name="Switzerland", population=7581520, continent=continent)
    >>> country.save()
    >>> see = Place(name="Zurichsee", country=country, latitude="41.003738", longitude="59.238281")
    >>> see.save()
    >>> mountain = Place(name="Zermatt", country=country, latitude="46.456098", longitude="10.971222")
    >>> mountain.save()
    
    >>> bob = User(username="bob")
    >>> bob.save()
    
    >>> france = Country(name="France", population= 61538322, continent=continent)
    >>> france.save()
    >>> paris = Place(name="Paris", country=france, latitude="46.019265", longitude="7.745973")
    >>> paris.save()
    
    >>> french_guy = Person(user=bob, current_location=paris)
    >>> french_guy.save()
    >>> french_guy.favorite_places.add(see)
    >>> french_guy.favorite_places.add(mountain)
    
    >>> safe_places = Destination(name="Safe places")
    >>> safe_places.save()
    >>> safe_city = Destination(name="Zurich", parent=safe_places, place=see)
    >>> safe_city.save()
    
    >>> capitals = Destination(name="Capital city")
    >>> capitals.save()
    >>> capital_city = Destination(name="Paris", parent=capitals, place=paris)
    >>> capital_city.save()
    
    >>> Destination.objects.all()
    [<Destination: Safe places>, <Destination: Zurich>, <Destination: Capital city>, <Destination: Paris>]
    
    >>> Destination.objects.get(pk=safe_places.id).children.all()
    [<Destination: Zurich>]
    
    # publish safe_city
    >>> pub_safe_city = safe_city.publish()
    >>> Destination.Public.objects.get(pk=pub_safe_city.id)
    <PublicDestination: Zurich>
    
    """ 
    name = models.CharField(max_length=128, null=True, blank=True)
    place = models.ForeignKey(Place, null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    
    class Meta:
        verbose_name=_('Destination')
        verbose_name_plural=_('Destinations')
    
    __unicode__ = lambda self: self.name or unicode(self.place)