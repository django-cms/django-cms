from django.conf import settings
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields.related import RelatedField, OneToOneRel
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

    def get_object_queryset(self):
        """Returns smart queryset depending on object type - draft / public
        """
        qs = self.__class__.objects
        return self.publisher_is_draft and qs.drafts() or qs.public()

    def save_base(self, *args, **kwargs):
        """Overriden save_base. If an instance is draft, and was changed, mark
        it as dirty.

        Dirty flag is used for changed nodes identification when publish method
        takes place. After current changes are published, state is set back to
        PUBLISHER_STATE_DEFAULT (in publish method).
        """
        keep_state = getattr(self, '_publisher_keep_state', None)

        if self.publisher_is_draft and not keep_state:
            self.publisher_state = Publisher.PUBLISHER_STATE_DIRTY
        if keep_state:
            delattr(self, '_publisher_keep_state')

        ret = super(Publisher, self).save_base(*args, **kwargs)
        return ret

    def _publisher_can_publish(self):
        """Checks if instance can be published.
        """
        return True

    def _publisher_get_public_copy(self):
        """This is here because of the relation between CMSPlugins - model
        inheritance.

        eg. Text.objects.get(pk=1).publisher_public returns instance of CMSPlugin
        instead of instance of Text, thats why this method must be overriden in
        CMSPlugin.
        """
        return self.publisher_public

    def publish(self, excluded_models=None, first_instance=True):
        """Publish current instance

        Args:
            - excluded_models: list of classes (models) which should be
                inherited into publishing proces - this is used internally - if
                instance haves relation to self, or there is any cyclic relation
                back to current model, this relation will not be included.

        Returns: published instance
        """

        ########################################################################
        # perform checks
        if not self.publisher_is_draft:
            # it is public instance, there isn't anything to publish, just escape
            return

#        assert self.pk is not None, "Can publish only saved instance, save it first."
        if not self.pk:
            self.save()

        if not self._publisher_can_publish():
            raise PublisherCantPublish

        fields = self._meta.fields

        if excluded_models is None:
            excluded_models = []
        excluded_models.append(self.__class__)

        ########################################################################
        # publish self and related fields
        public_copy, created = self._publisher_get_public_copy(), False

        if not public_copy:
            public_copy, created = self.__class__(publisher_is_draft=False), True

        for field in fields:
            if field.name in self._publisher_meta.exclude_fields:
                continue

            value = getattr(self, field.name)
            if isinstance(field, RelatedField):
                related = field.rel.to
                if issubclass(related, Publisher):
                    if not related in excluded_models and value:
                        value = value.publish(excluded_models=excluded_models, first_instance=False)
                    elif value:
                        value = value.publisher_public
            try:
                setattr(public_copy, field.name, value)
            except ValueError:
                pass

        ########################################################################
        # perform saving
        # publish copy - all behind this requires public instance to have pk

        self._publisher_save_public(public_copy)

        # store public model relation for current instance (only) for newly
        # created items

        # insert_at() was maybe calling _create_tree_space() method, in this
        # case may tree_id change, so we must update tree_id from db first
        # before save
        if getattr(self, 'tree_id', None):
            me = self._default_manager.get(pk=self.pk)
            self.tree_id = me.tree_id

        if created:
            self.publisher_public = public_copy

        # save changes, i'm not dirty anymore
        self.publisher_state = Publisher.PUBLISHER_STATE_DEFAULT
        self._publisher_keep_state = True
        self.save_base(cls=self.__class__)

        ########################################################################
        # update many to many relations
        for field in self._meta.many_to_many:
            name = field.name
            if name in self._publisher_meta.exclude_fields:
                continue

            m2m_manager = getattr(self, name)
            public_m2m_manager = getattr(public_copy, name)

            updated_obj_ids = []

            from django.contrib.contenttypes import generic
            if isinstance(field, generic.GenericRelation):
                continue

            # just the dirty objects
            for obj in m2m_manager.all():
                remote_pk = obj.pk
                # is this object already published?

                if issubclass(obj.__class__, Publisher):
                    # is the related object under publisher?
                    remote_pk = obj.publisher_public_id
                    if not obj.publisher_public_id:
                        # publish it first...
                        obj = obj.publish(excluded_models=excluded_models, first_instance=False)
                        remote_pk = obj.pk

                updated_obj_ids.append(remote_pk)
                public_m2m_manager.add(obj)
                # save obj if it was dirty
                if obj.publisher_state == Publisher.PUBLISHER_STATE_DIRTY:
                    self.publisher_state = Publisher.PUBLISHER_STATE_DEFAULT
                    self._publisher_keep_state = True
                    obj.save_base(cls=obj.__class__)

            # remove all not updated instances
            # we have to do this, because m2m doesn't have dirty flag, and
            # maybe there was some change in m2m relation
            unupdated = public_m2m_manager.exclude(pk__in=updated_obj_ids)
            public_m2m_manager.remove(*unupdated)
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
                    try:
                        # this is a reverse relation, in may happen, that we
                        # are trying to publish something we are not allow to,
                        # thats why IntegrityError may be received in case when
                        # it is not possible to publish this object
                        item.publish(excluded_models=excluded_models + [obj.__class__], first_instance=False)
                    except:
                        pass

        # perform cleaning on public copy, if instance id marked for deletion,
        # delete it
        if not created and first_instance:
            # perform cleaning if required, makes sense only for already
            # existing instances
            public_copy._publisher_delete_marked()
        return public_copy

    def _publisher_save_public(self, obj):
        """Save method for object which should be published. obj is a instance
        of the same class as self.
        """
        return obj.save()

    def _collect_delete_marked_sub_objects(self, seen_objs, parent=None, nullable=False, excluded_models=None):
        if excluded_models is None:
            excluded_models = [self.__class__]
        elif not isinstance(self, Publisher) or self.__class__ in excluded_models:
            return

        pk_val = self._get_pk_val()
        if seen_objs.add(self.__class__, pk_val, self, parent, nullable):
            return

        for related in self._meta.get_all_related_objects():
            rel_opts_name = related.get_accessor_name()

            if not issubclass(related.model, Publisher) or related.model in excluded_models:
                continue

            if isinstance(related.field.rel, OneToOneRel):
                try:
                    sub_obj = getattr(self, rel_opts_name)
                except ObjectDoesNotExist:
                    pass
                else:
                    sub_obj._collect_delete_marked_sub_objects(seen_objs, self.__class__, related.field.null, excluded_models=excluded_models)
            else:
                # To make sure we can access all elements, we can't use the
                # normal manager on the related object. So we work directly
                # with the descriptor object.
                for cls in self.__class__.mro():
                    if rel_opts_name in cls.__dict__:
                        rel_descriptor = cls.__dict__[rel_opts_name]
                        break
                else:
                    raise AssertionError("Should never get here.")
                delete_qs = rel_descriptor.delete_manager(self).all()
                #filter(publisher_state=Publisher.PUBLISHER_STATE_DELETE)
                for sub_obj in delete_qs:
                    if not isinstance(sub_obj, Publisher) or sub_obj.__class__ in excluded_models:
                        continue
                    sub_obj._collect_delete_marked_sub_objects(seen_objs, self.__class__, related.field.null, excluded_models=excluded_models)

        # Handle any ancestors (for the model-inheritance case). We do this by
        # traversing to the most remote parent classes -- those with no parents
        # themselves -- and then adding those instances to the collection. That
        # will include all the child instances down to "self".
        parent_stack = [p for p in self._meta.parents.values() if p is not None]
        while parent_stack:
            link = parent_stack.pop()
            parent_obj = getattr(self, link.name)
            if parent_obj._meta.parents:
                parent_stack.extend(parent_obj._meta.parents.values())
                continue
            # At this point, parent_obj is base class (no ancestor models). So
            # delete it and all its descendents.

            parent_obj._collect_delete_marked_sub_objects(seen_objs, excluded_models=excluded_models)


    def _publisher_delete_marked(self, collect=True):
        """If this instance, or some remote instances are marked for deletion
        kill them.
        """
        if self.publisher_is_draft:
            # escape soon from draft models
            return

        if collect:
            from django.db.models.query import CollectedObjects
            seen = CollectedObjects()
            self._collect_delete_marked_sub_objects(seen)
            for cls, items in seen.items():
                if issubclass(cls, Publisher):
                    for item in items.values():
                        item._publisher_delete_marked(collect=False)

        if self.publisher_state == Publisher.PUBLISHER_STATE_DELETE:
            try:
                self.delete()
            except AttributeError:
                # this exception may happen because of the plugin relations
                # to CMSPlugin and mppt way of _meta assignment
                pass

    def delete(self):
        """Mark public instance for deletion and delete draft.
        """
        if self.publisher_public_id:
            # mark the public instance for deletion
            self.publisher_public.publisher_state = Publisher.PUBLISHER_STATE_DELETE
            self.publisher_public.save()
        super(Publisher, self).delete()

    def delete_with_public(self):
        if self.publisher_public_id:
            self.publisher_public.delete()
        super(Publisher, self).delete()


class MpttPublisher(Publisher, Mptt):
    class Meta:
        abstract = True

    class PublisherMeta:
        exclude_fields = []
        exclude_fields_append = ['id', 'lft', 'rght', 'tree_id', 'parent']


    def get_next_filtered_sibling(self, **filters):
        """Very simillar to original mptt method, but adds support for filters.
        Returns this model instance's next sibling in the tree, or
        ``None`` if it doesn't have a next sibling.
        """
        opts = self._meta
        if self.is_root_node():
            filters.update({
                '%s__isnull' % opts.parent_attr: True,
                '%s__gt' % opts.tree_id_attr: getattr(self, opts.tree_id_attr),
            })
        else:
            filters.update({
                 opts.parent_attr: getattr(self, '%s_id' % opts.parent_attr),
                '%s__gt' % opts.left_attr: getattr(self, opts.right_attr),
            })

        sibling = None
        try:
            sibling = self._tree_manager.filter(**filters)[0]
        except IndexError:
            pass
        return sibling

    def get_previous_fitlered_sibling(self, **filters):
        """Very simillar to original mptt method, but adds support for filters.
        Returns this model instance's previous sibling in the tree, or
        ``None`` if it doesn't have a previous sibling.
        """
        opts = self._meta
        if self.is_root_node():
            filters.update({
                '%s__isnull' % opts.parent_attr: True,
                '%s__lt' % opts.tree_id_attr: getattr(self, opts.tree_id_attr),
            })
            order_by = '-%s' % opts.tree_id_attr
        else:
            filters.update({
                 opts.parent_attr: getattr(self, '%s_id' % opts.parent_attr),
                '%s__lt' % opts.right_attr: getattr(self, opts.left_attr),
            })
            order_by = '-%s' % opts.right_attr

        sibling = None
        try:
            sibling = self._tree_manager.filter(**filters).order_by(order_by)[0]
        except IndexError:
            pass
        return sibling

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

        Args:
            obj - public variant of `self` to be saved.

        """
        last_base = self.__class__.mro()[1]
        if not last_base in (Publisher, MpttPublisher):
            # special case, is an inherited mptt, use normal save
            return super(MpttPublisher, self)._publisher_save_public(obj)

        prev_sibling = self.get_previous_fitlered_sibling(publisher_is_draft=True, publisher_public__isnull=False)

        if not self.publisher_public_id:
            # is there anybody on left side?
            if prev_sibling:
                obj.insert_at(prev_sibling.publisher_public, position='right', commit=False)
            else:
                # it is a first time published object, perform insert_at:
                parent, public_parent = self.parent, None
                if parent:
                    public_parent = parent.publisher_public
                if public_parent:
                    obj.insert_at(public_parent, commit=False)
        else:
            # check if object was moved / structural tree change
            prev_public_sibling = obj.get_previous_fitlered_sibling()

            if not self.level == obj.level or \
                not (self.level > 0 and self.parent.publisher_public == obj.parent) or \
                not prev_sibling == prev_public_sibling == None or \
                (prev_sibling and prev_sibling.publisher_public_id == prev_public_sibling.id):

                if prev_sibling:
                    obj.move_to(prev_sibling.publisher_public, position="right")
                elif self.parent:
                    # move as a first child to parent
                    target = self.parent.publisher_public
                    obj.move_to(target, position='first-child')
                else:
                    # it is a move from the right side or just save
                    next_sibling = self.get_next_filtered_sibling(publisher_is_draft=True, publisher_public__isnull=False)
                    if next_sibling and next_sibling.publisher_public_id:
                        obj.move_to(next_sibling.publisher_public, position="left")
        # or none structural change, just save
        return obj.save()

# install publisher on first import from this module...
install_publisher()

