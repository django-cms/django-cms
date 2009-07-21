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
from django.db.models.fields.related import RelatedField
from publisher.base import install_publisher
from publisher.manager import PublisherManager
from publisher.errors import MpttPublisherCantPublish, PublisherCantPublish
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
        """There are following options for publisher meta class:
        
        - exclude_fields: excludes just given fields, if given, overrides all
            already excluded fields - they don't inherit from parents anymore
        
        - exlude_fields_append: appends given fields to exclude_fields set 
            inherited from parents, if there are some
        """
        
        exclude_fields = ['id', 'publisher_is_draft', 'publisher_public', 'publisher_state']
        exclude_fields_append = []
    
    
    def save_base(self, *args, **kwargs):
        """Overriden save_base. If an instance is draft, and was changed, mark
        it as dirty.
        
        Dirty flag is used for changed nodes identification when publish method
        takes place. After current changes are published, state is set back to
        PUBLISHER_STATE_DEFAULT (in publish method).
        """
        if self.publisher_is_draft:
            self.publisher_state = Publisher.PUBLISHER_STATE_DIRTY
        print ">> page.save_base pre", self.publisher_is_draft
        ret = super(Publisher, self).save_base(*args, **kwargs)
        print ">> page.save_base post", self.publisher_is_draft
        return ret
    
    def _publisher_can_publish(self):
        """Checks if instance can be published.
        """
        return True
    
    '''
    def _publisher_copy_simple(self, fields, exclude):
        pass
    
    def _publisher_copy_m2m(self):
        pass
    
    def _publisher_copy_fk(self):
        pass
    '''
    
    def _publisher_get_public_copy(self):
        """This is here because of the relation between CMSPlugins - model 
        inheritance. 
        
        eg. Text.objects.get(pk=1).publisher_public returns instance of CMSPlugin
        instead of instance of Text, thats why this method must be overriden in 
        CMSPlugin.
        """
        return self.publisher_public
    
    def publish(self, excluded_models=None):
        """Publish current instance
        
        Args:
            - excluded_models: list of classes (models) which should be 
                inherited into publishing proces - this is used internally - if 
                instance haves relation to self, or there is any cyclic relation 
                back to current model, this relation will not be included.
                 
        Returns: published instance
        """
        
        print "\n", "-" * 30, "publish:", self.__class__.__name__, "-" * 30
        
        
        ########################################################################
        # perform checks
        if not self.publisher_is_draft:
            # it is public instance, there isn't anything to publish, just escape
            print ">> publish escape because draft.."
            return
        
        assert self.pk is not None, "Can publish only saved instance, save it first."
        
        print ">> publishing A.."
        
        if not self._publisher_can_publish():
            raise PublisherCantPublish
        
        fields = self._meta.fields
        
        if excluded_models is None:
            excluded_models = []
        excluded_models.append(self.__class__)
        
        print ">> publishing B.."
        ########################################################################
        # publish self and related fields
        public_copy, created = self._publisher_get_public_copy(), False
        
        print ">> GPC:", public_copy
        
        if not public_copy:
            print ">> NPC"
            public_copy, created = self.__class__(publisher_is_draft=False), True
        
        print ">> KLASS:", public_copy.__class__
        
        print "EX", self._publisher_meta.exclude_fields
        
        for field in fields:
            if field.name in self._publisher_meta.exclude_fields:
                continue
            
            value = getattr(self, field.name)
            if isinstance(field, RelatedField):
                related = field.rel.to
                if issubclass(related, Publisher):
                    print ">> got related...", related
                    print "----------------"
                    if not related in excluded_models and value:
                        # can follow
                        #try:
                        print ">>> must publish:", value
                        value = value.publish(excluded_models=excluded_models)
                        #except MpttCantPublish:
                        #    pass
                    elif value:
                        value = value.publisher_public
            
            print ">> FIELD:", field.name, ":",  value
            setattr(public_copy, field.name, value)        
        
        print ">> publishing.. saving with pk:", public_copy.pk, public_copy.__class__
        ########################################################################
        # perform saving
        
        # publish copy - all behind this requires public instance to have pk
        
        self._publisher_save_public(public_copy)
        
        
        print ">> publishing C 1..", self.pk, public_copy.pk
        # store public model relation for current instance (only) for newly 
        # created items
        if created:
            self.publisher_public = public_copy
        print ">> publishing C 2.."
        # i'm not dirty anymore
        self.publisher_state = Publisher.PUBLISHER_STATE_DEFAULT
        
        print ">> publishing C 3.."
        # save changes
        self.save_base(cls=self.__class__)
        
        print ">> publishing D.."
        ########################################################################
        # update many to many relations
        for field in self._meta.many_to_many:
            name = field.name
            if name in self._publisher_meta.exclude_fields:
                continue
            
            m2m_manager = getattr(self, name)
            public_m2m_manager = getattr(public_copy, name)
            
            updated_obj_ids = []
            
            # just the dirty objects
            for obj in m2m_manager.all():
                remote_pk = obj.pk
                # is this object already published? 
                if issubclass(obj.__class__, Publisher):
                    # is the related object under publisher?
                    remote_pk = obj.publisher_public_id
                    if not obj.publisher_public_id:
                        # publish it first...
                        remote = obj.publish(excluded_models=excluded_models)
                        remote_pk = remote.pk
                    
                    updated_obj_ids.append(remote_pk)
                public_m2m_manager.add(remote_pk)
                
                # save obj if it was dirty
                if obj.publisher_state == Publisher.PUBLISHER_STATE_DIRTY:
                    obj.publisher_state = Publisher.PUBLISHER_STATE_DEFAULT
                    obj.save_base(cls=obj.__class__)
            
            # remove all not updated instances
            # we have to do this, because m2m doesn't have dirty flag, and
            # maybe there was some change in m2m relation
            public_m2m_manager.exclude(pk__in=updated_obj_ids).remove()
                
        print ">> publishing E.."
        ########################################################################
        # update related objects (FK) / model inheritance
        for obj in self._meta.get_all_related_objects():
            if obj.model in excluded_models:
                continue
            #excluded_models.append(obj.__class__)
            if issubclass(obj.model, Publisher):
                # get all objects for this, and publish them
                name = obj.get_accessor_name()
                if name in self._publisher_meta.exclude_fields:
                    continue
                try:
                    try:
                        item_set = getattr(self, name).all()
                    except AttributeError:
                        item_set = [getattr(self, name)] # for model inheritance
                except ObjectDoesNotExist:
                    continue
                for item in item_set:
                    item.publish(excluded_models=excluded_models + [obj.__class__])
        
        print ">> publishing done..."
        return public_copy
        
    
    def _publisher_save_public(self, obj):
        """Save method for object which should be published. obj is a instance 
        of the same class as self. 
        """
        print "publisher._publisher_save_public()"
        return obj.save() 
        
    
    def delete(self):
        """Delete public instance first!
        """
        if self.publisher_public_id:
            self.publisher_public.delete()
        super(Publisher, self).delete()
        
     
        
    
class MpttPublisher(Publisher, Mptt):
    class Meta:
        abstract = True

    class PublisherMeta:
        exclude_fields = []
        exclude_fields_append = ['id', 'lft', 'rght', 'tree_id', 'parent']
    
    
    def _get_prev_sibling(self, **filters):
        """Returns object previous sibling or None if object doesn't haves one
        """
        filters.update({
            'lft__lt': self.lft,
        })
        
        try:
            return self.get_siblings().filter(**filters).order_by('-lft')[0]
        except IndexError:
            pass
        return None
    
    
    def _publisher_can_publish(self):
        """Is parent of this object already published?
        """
        if self.parent_id:
            try:
                return bool(self.parent.publisher_public_id)
            except AttributeError:
                raise MpttPublisherCantPublish
        return True
        
    def _publisher_save_public(self, obj):
        """Mptt specific stuff before the object can be saved, overrides original
        publisher method.
        """
        last_base = self.__class__.mro()[1]
        print "MRO:", self.__class__.mro()
        if not last_base in (Publisher, MpttPublisher):
            # special case, is an inherited mptt, use normal save
            print ">> roll back to publisher.publisher_save_... ", last_base
            return super(MpttPublisher, self)._publisher_save_public(obj)
        
        print ">> mptt.publish._publisher_save_public()"
        if not self.publisher_public_id:
            print "-- mptt - new public instance"
            # it is a first time published object, perform insert_at:
            parent, public_parent = self.parent, None
            if parent:
                public_parent = parent.publisher_public
            if public_parent:
                print ">> _mptt.insert_at()", public_parent.id
                obj.insert_at(public_parent, commit=False)
            print ">> _mptt.save()"
        else:
            # check if object was moved / structural tree change
            prev_sibling = self._get_prev_sibling(publisher_public__isnull=False)
            prev_public_sibling = obj._get_prev_sibling()
            
            print "siblings:", prev_sibling, "-", prev_public_sibling
            
            if not self.level == obj.level or \
                not (self.level > 0 and self.parent.publisher_public == obj.parent) or \
                not prev_sibling == prev_public_sibling == None or \
                (prev_sibling and prev_sibling.publisher_public_id == prev_public_sibling.id):
            
            #if not (self.level == obj.level and \
            #    (prev_sibling == prev_public_sibling == None or \
            #    (prev_sibling and prev_public_sibling and prev_sibling.publisher_public_id == prev_public_sibling.id))):
                
                print "-- mptt moved instance"
                
                if prev_sibling is None and self.parent:
                    # move as a first child to parent
                    target = self.parent.publisher_public
                    print "-- mptt move_to as a first-child under parent:", target
                    obj.move_to(target, position='first-child')
                elif prev_sibling:
                    print "-- mptt move_to on right side from:", prev_sibling.publisher_public
                    obj.move_to(prev_sibling.publisher_public, position="right")
            else:
                print "-- mptt new/updated instance"
        # otherwise none structural changes, just save
        return obj.save()

# install publisher on first import from this module...
install_publisher()