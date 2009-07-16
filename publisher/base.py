from copy import deepcopy
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.loading import get_model
from django.db.models.fields.related import RelatedField
from django.core.exceptions import ObjectDoesNotExist
from publisher.errors import MpttCantPublish


class Publisher(models.Model):
    """Abstract class which have to be extended for adding class to publisher.
    """
    def publish(self, fields=None, exclude=None):
        """Publish current instance
        
        Args:
            - fields: list of field names which shuld be taken, if None uses
                all fields
            - exclude: list of classes (models) which should be inherited into
                publishing proces - this is used internally - if instance haves
                relation to self, or there is any cyclic relation back to 
                current model, this relation will not be included.
                 
        Returns: published instance
        """
        
        assert self.pk is not None, "Can publish only saved instance, save it first."
        
        if hasattr(self, "mptt_can_publish") and not self.mptt_can_publish():
            # this model is also mptt model, and self.parent isn't published
            raise MpttCantPublish
        
        if fields is None:
            fields = self._meta.fields
        
        if exclude is None:
            exclude = []
        
        exclude.append(self.__class__)
        
        created = False
        public_copy = None
        
        try:
            try:
                public_copy = self.public
            except AttributeError:
                public_copy = self.inherited_public
        except ObjectDoesNotExist:
            pass
        
        if not public_copy:
            created = True
            public_copy = self.__class__.PublicModel()    
        for field in fields:
            value = getattr(self, field.name)
            if isinstance(field, RelatedField):
                if field.name in ('public', 'inherited_public'):
                    continue
                related = field.rel.to
                if issubclass(related, Publisher):
                    if not related in exclude and value:
                        # can follow
                        try:
                            value = value.publish(exclude=exclude)
                        except MpttCantPublish:
                            pass
                    elif value:
                        # if somethings wrong, we may get some erorr here in case
                        # when target isn't publihsed
                        try:
                            value = value.public
                        except AttributeError:
                            value = value.inherited_public
            setattr(public_copy, field.name, value)        
        # publish copy
        self.publish_save(public_copy)
        
        if created:
            # store data about public model
            if hasattr(self, 'public'):
                self.public = public_copy
            if hasattr(self, 'inherited_public'):
                self.inherited_public = public_copy
            self.save_base(cls=self.__class__)
        
        # update many to many relations
        for field in self._meta.many_to_many:
            name = field.name
            m2m_manager = getattr(self, name)
            public_m2m_manager = getattr(public_copy, name)
            
            # clear public manager first!
            public_m2m_manager.remove()
            
            for obj in m2m_manager.all():
                public_m2m_manager.add(obj.pk)
            
        # update related objects (FK) / model inheritance
        for obj in self._meta.get_all_related_objects():
            if obj.model in exclude:
                continue
            #exclude.append(obj.__class__)
            if issubclass(obj.model, Publisher):
                # get all objects for this, and publish them
                name = obj.get_accessor_name()
                try:
                    try:
                        item_set = getattr(self, name).all()
                    except AttributeError:
                        item_set = [getattr(self, name)] # for model inheritance
                except ObjectDoesNotExist:
                    continue
                for item in item_set:
                    item.publish(exclude=exclude + [obj.__class__])
        
        if not created:
            # check if there is something marked for delete in public model
            public_copy.delete_marked_for_deletion()
        return public_copy
        
    
    def publish_save(self, copy):
        """Save method for object which should be published. Received instance
        of public model as an argument, use save_base - never use original save
        method.
        """
        saved = copy.save_base(cls=copy.__class__)
        #if hasattr(self, 'update_after_save'):
        #    self.update_after_save()
        return saved 
        
    
    def delete(self):
        """Mark published object for deletion first.
        """
        try:
            public = self.public
        except AttributeError:
            try:
                public = self.inherited_public
            except AttributeError:
                public = None
    
        if public:
            public.mark_delete=True
            public.save_base(cls=public.__class__)
    
        super(Publisher, self).delete()
    
    
    def delete_with_public(self):
        try:
            public = self.public
        except AttributeError:
            public = self.inherited_public

        if public:
            public.delete()
        self.delete()        
    
    class Meta:
        abstract = True


class PublicPublisher(models.Model):
    """This will be always added to public mode bases.
    """
    def delete_marked_for_deletion(self, collect=True):
        """If this instance, or some remote instances are marked for deletion
        kill them.
        """
        if collect:
            from django.db.models.query_utils import CollectedObjects
            
            seen = CollectedObjects()
            
            self._collect_sub_objects(seen)
            for cls, items in seen.items():
                if issubclass(cls, PublicPublisher):
                    for item in items.values():
                        item.delete_marked_for_deletion(collect=False)
                    
        if self.mark_delete:
            self.delete()

    class Meta:
        abstract = True
        

class Mptt(models.Model):
    """Abstract class which have to be extended for installing mptt on class. 
    For changing attributes see MpttMeta
    """
    class Meta:
        abstract = True
        
    def mptt_can_publish(self):
        """Returns current state of mptt node - if it can be published.
        In case when node parent exists, check if parent is published.
        """
        try:
            return bool(self.parent.public)
        except ObjectDoesNotExist:
            return False
        except AttributeError:
            pass
        return True
            

def install_publisher():
    """Check if publisher isn't installed already, install it otherwise. But 
    install it only once.
    """
    from publisher.mptt_support import install_mptt, finish_mptt
    
    _old_new = ModelBase.__new__
    def publisher_modelbase_new(cls, name, bases, attrs):
        """Override modelbase new method, check if Publisher attribute is
        subclass of Publisher.
        """
        
        # in case of model inheritance
        base_under_publisher = bool(filter(lambda b: issubclass(b, Publisher), bases))
        
        is_publisher_model = Publisher in bases or base_under_publisher
        
        if is_publisher_model:
            attrs['_is_publisher_model'] = lambda self: True
            
        """
        if Publisher in bases or base_under_publisher:            
            # copy attrs, because ModelBase affects them
            public_attrs = deepcopy(attrs)
            
            attrs['_is_publisher_model'] = lambda self: True
                        
            # create proxy - accessor for public model
            class PublicModelProxy(object):
                def __get__(self, name, cls):
                    public_name = PublisherManager.PUBLISHER_MODEL_NAME % cls._meta.object_name
                    model = get_model(cls._meta.app_label, public_name.lower())
                    return model
            
            attrs['PublicModel'] = PublicModelProxy()
        
        # take care of mptt, if required
        """
        
        attrs = install_mptt(cls, name, bases, attrs)
        new_class = _old_new(cls, name, bases, attrs)
        
        if is_publisher_model:
            # register it for future use..., @see publisher.post
            if not base_under_publisher:
                public_bases = list(bases)
                public_bases.remove(Publisher)
                if not public_bases:
                    public_bases = (models.Model,)
            else:
                public_bases = bases
            publisher_manager.register(cls, name, tuple(public_bases), public_attrs, new_class)
        
        finish_mptt(new_class)
        
        return new_class
    
    ModelBase.__new__ = staticmethod(publisher_modelbase_new)
    
    ModelBase._publisher_installed = True
    
# install publisher on first import from this module...
#from publisher.core import install_publisher
install_publisher()