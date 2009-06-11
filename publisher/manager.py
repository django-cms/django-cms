from django.db import models
from django.db.models.base import ModelBase
from django.db.models.loading import get_model
from django.db.models.fields.related import RelatedField, add_lazy_relation
    
class PublisherManager(object):
    # common prefix for public class names
    PUBLISHER_MODEL_NAME = "Public%s"
    
    registry = []

    # items from this will be pop-ed, so will be empty when we are done
    creation_registry = []
    inherited = []
    
    def register(self, cls, model_name, bases, attrs, origin_cls):
        # already registered?
        if origin_cls in self.registry:
            return
        
        # just append the model to registry, the rest will be made after the
        # publisher.post models are installed
        self.registry.append(origin_cls)
        self.creation_registry.append((cls, model_name, bases, attrs, origin_cls))
        
        for base in bases:
            if base in self.registry:
                self.inherited.append(base) # mark all inherited classes

    def install(self):
        """This must be called after creation of all other models, thats why publisher
        must be last application in installed apps.
        """
        i = 0
        while i < len(self.creation_registry):
            print "  GW:", self.creation_registry[i][1]
            item = self.creation_registry[i]
            if self._create_public_model(*item):
                self.creation_registry.pop(i)
            else:
                i += 1
                    
    def _create_public_model(self, cls, name, bases, attrs, origin_cls):
        from publisher.base import Publisher, PublicPublisher
        
        # because of model inheritance
        rebased = []
        for base in bases:
            if issubclass(base, Publisher) and base in self.registry:
                # rebase it to public model
                print ">> rebase base:", base, ">", base.PublicModel
                base = base.PublicModel
                if not base:
                    # inherited model isnt't registered yet, escape
                    return
            rebased.append(base)
        
        if not rebased:
            rebased = list(bases)
        
        if not PublicPublisher in rebased:
            rebased.append(PublicPublisher)
        
        print "\n>> create public model:", name, "-" * 20
        
        for attr, value in attrs.items():
            if isinstance(value, RelatedField):
                self.other = value.rel.to
                
                # is this still required...?
                if isinstance(self.other, basestring):
                    def resolve_other(field, model, cls):
                        self.other = model
                    # all standards models are already created in this time, so it 
                    # should'nt do any lazy operation
                    add_lazy_relation(origin_cls, value, self.other, resolve_other)
                
                # get model to which points this relation
                model = get_model(self.other._meta.app_label, self.other._meta.object_name.lower(), False)
                if issubclass(model, Publisher):
                    # it is a subclass of Publisher, change relation
                    relation_public_name = PublisherManager.PUBLISHER_MODEL_NAME % self.other._meta.object_name
                    print "R >>", self.other, "remap:", self.other._meta.object_name, "=>", relation_public_name
                    
                    to = model.PublicModel or relation_public_name
                    attrs[attr].rel.to = to
        
        #if not inherited:
        #    attrs['origin'] = models.OneToOneField(origin_cls, related_name="public")
        
        # setup one to one relation to origin model
        '''
        if not origin_cls in self.inherited:
            # skip links for inherited models   
            attrs['origin'] = models.OneToOneField(origin_cls, related_name="public", null=True, blank=True)
        else:
            attrs['inherited_origin'] = models.OneToOneField(origin_cls, related_name="inherited_public", null=True, blank=True)
        '''
        # mark it as public model, so we can recognize it when required 
        attrs['_is_public_model'] = lambda self: True
        
        # construct class
        public_name = PublisherManager.PUBLISHER_MODEL_NAME % name
        public_cls = ModelBase.__new__(cls, public_name, tuple(rebased), attrs)
        
        if not 'mark_delete' in [field.name for field in public_cls._meta.local_fields]:
            field = models.BooleanField(default=False)
            public_cls.add_to_class('mark_delete', field)
            
        
        if not origin_cls in self.inherited:
            # skip links for inherited models   
            #attrs['origin'] = models.OneToOneField(origin_cls, related_name="public", null=True, blank=True)
            origin_cls.add_to_class('public', models.OneToOneField(public_cls, related_name="origin", null=True, blank=True))
        else:
            #attrs['inherited_origin'] = models.OneToOneField(origin_cls, related_name="inherited_public", null=True, blank=True)
            origin_cls.add_to_class('inherited_public', models.OneToOneField(public_cls, related_name="inherited_origin", null=True, blank=True))
        
        print "origin field:", public_name, ">", origin_cls
        
        #origin_cls.add_to_class('public_model', public_cls)
        
        print ">>> cpm:", public_cls, origin_cls.PublicModel
        return True
        
publisher_manager = PublisherManager()