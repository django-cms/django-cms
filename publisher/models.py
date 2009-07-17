'''
import publisher
if not getattr(publisher,'_ready', False):
    """
    the first time this module is loaded by django it raises an
    ImportError. this forces it into the postponed list and it will
    be called again later (after the other postponed apps are loaded.)
    """
    publisher._ready = True
    raise ImportError("Not ready yet")
from publisher.manager import publisher_manager
publisher_manager.install()
'''
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from publisher.base import install_publisher
from publisher.manager import PublisherManager
from publisher.errors import MpttCantPublish
from publisher.mptt_support import Mptt


class Publisher(models.Model):
    """Abstract class which have to be extended for adding class to publisher.
    """    
    PUBLISHER_STATE_DEFAULT = 0
    PUBLISHER_STATE_DIRTY = 1
    PUBLISHER_STATE_DELETE = 2
    
    publisher_is_draft = models.BooleanField(default=1, editable=False, db_index=True)
    publisher_public = models.OneToOneField('self', related_name='publisher_draft',  null=True, editable=False)
    publisher_state = models.SmallIntegerField(default=0, editable=False, db_index=True)
    
    objects = PublisherManager()
    
    class Meta:
        abstract = True
    
    class PublisherMeta:
        """There are following options for publusher meta class:
        
        - exclude_fields: excludes just given fields, if given, overrides all
            already excluded fields - they don't inherit from parents anymore
        
        - exlude_fields_append: appends given fields to exclude_fields set 
            inherited from parents, if there are some
        """
        
        exclude_fields = ['pk']
        exclude_fields_append = []
    
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
        return
        
        assert self.pk is not None, "Can publish only saved instance, save it first."
        assert self.publisher_is_draft is not True, "Only draft model can be published."
        
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
        """Delete public instance first!
        """
        if self.publisher_public_id:
            self.publisher_public.delete()
        super(Publisher, self).delete()
        
    
class MpttPublisher(Mptt, Publisher):
    class Meta:
        abstract = True

    class PublisherMeta:
        exclude_fields = ['pk', 'lft', 'rght', 'tree_id', 'parent']
        exclude_fields_append = []

    def can_publish(self):
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

# install publisher on first import from this module...
install_publisher()