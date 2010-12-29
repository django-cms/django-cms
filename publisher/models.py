from publisher.errors import MpttPublisherCantPublish
from publisher.mptt_support import Mptt


class MpttPublisher(Mptt):
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
        if last_base != MpttPublisher:
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
        obj.save()
        return obj