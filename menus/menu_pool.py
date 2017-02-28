# -*- coding: utf-8 -*-
import warnings
from functools import partial
from logging import getLogger

from django.conf import settings
from django.contrib import messages
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.urlresolvers import NoReverseMatch
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _

from cms.utils import get_cms_setting
from cms.utils.django_load import load

from menus.base import Menu
from menus.exceptions import NamespaceAlreadyRegistered
from menus.models import CacheKey

import copy

logger = getLogger('menus')


def _build_nodes_inner_for_one_menu(nodes, menu_class_name):
    '''
    This is an easier to test "inner loop" building the menu tree structure
    for one menu (one language, one site)
    '''
    done_nodes = {}  # Dict of node.id:Node
    final_nodes = []

    # This is to prevent infinite loops - we need to compare the number of
    # times we see a specific node to "something", and for the time being,
    # it's the total number of nodes
    list_total_length = len(nodes)

    while nodes:
        # For when the node has a parent_id but we haven't seen it yet.
        # We must not append it to the final list in this case!
        should_add_to_final_list = True

        node = nodes.pop(0)

        # Increment the "seen" counter for this specific node.
        node._counter = getattr(node, '_counter', 0) + 1

        # Implicit namespacing by menu.__name__
        if not node.namespace:
            node.namespace = menu_class_name
        if node.namespace not in done_nodes:
            # We need to create the namespace dict to avoid KeyErrors
            done_nodes[node.namespace] = {}

        # If we have seen the parent_id already...
        if node.parent_id in done_nodes[node.namespace]:
            # Implicit parent namespace by menu.__name__
            if not node.parent_namespace:
                node.parent_namespace = menu_class_name
            parent = done_nodes[node.namespace][node.parent_id]
            parent.children.append(node)
            node.parent = parent
        # If it has a parent_id but we haven't seen it yet...
        elif node.parent_id:
            # We check for infinite loops here, by comparing the number of
            # times we "saw" this node to the number of nodes in the list
            if node._counter < list_total_length:
                nodes.append(node)
            # Never add this node to the final list until it has a real
            # parent (node.parent)
            should_add_to_final_list = False

        if should_add_to_final_list:
            final_nodes.append(node)
            # add it to the "seen" list
            done_nodes[node.namespace][node.id] = node
    return final_nodes


def _get_menu_class_for_instance(menu_class, instance):
    """
    Returns a new menu class that subclasses
    menu_class but is bound to instance.
    This means it sets the "instance" attribute of the class.
    """
    attrs = {'instance': instance}
    class_name = menu_class.__name__
    meta_class = type(menu_class)
    return meta_class(class_name, (menu_class,), attrs)


class MenuRenderer(object):
    # The main logic behind this class is to decouple
    # the singleton menu pool from the menu rendering logic.
    # By doing this we can be sure that each request has it's
    # private instance that will always have the same attributes.

    def __init__(self, pool, request):
        self.pool = pool
        # It's important this happens on init
        # because we need to make sure that a menu renderer
        # points to the same registered menus as long as the
        # instance lives.
        self.menus = pool.get_registered_menus(for_rendering=True)
        self.request = request

    def _build_nodes(self, site_id):
        """
        This is slow. Caching must be used.
        One menu is built per language and per site.

        Namespaces: they are ID prefixes to avoid node ID clashes when plugging
        multiple trees together.

        - We iterate on the list of nodes.
        - We store encountered nodes in a dict (with namespaces):
            done_nodes[<namespace>][<node's id>] = node
        - When a node has a parent defined, we lookup that parent in done_nodes
            if it's found:
                set the node as the node's parent's child (re-read this)
            else:
                the node is put at the bottom of the list
        """
        # Before we do anything, make sure that the menus are expanded.
        # Cache key management
        lang = get_language()
        prefix = getattr(settings, "CMS_CACHE_PREFIX", "menu_cache_")
        key = "%smenu_nodes_%s_%s" % (prefix, lang, site_id)
        if self.request.user.is_authenticated():
            key += "_%s_user" % self.request.user.pk
        cached_nodes = cache.get(key, None)
        if cached_nodes:
            return cached_nodes

        final_nodes = []
        toolbar = getattr(self.request, 'toolbar', None)
        for menu_class_name in self.menus:
            menu = self.get_menu(menu_class_name)

            try:
                nodes = menu.get_nodes(self.request)
            except NoReverseMatch:
                # Apps might raise NoReverseMatch if an apphook does not yet
                # exist, skip them instead of crashing
                nodes = []
                if toolbar and toolbar.is_staff:
                    messages.error(self.request,
                        _('Menu %s cannot be loaded. Please, make sure all '
                          'its urls exist and can be resolved.') %
                        menu_class_name)
                logger.error("Menu %s could not be loaded." %
                    menu_class_name, exc_info=True)
            # nodes is a list of navigation nodes (page tree in cms + others)
            final_nodes += _build_nodes_inner_for_one_menu(
                nodes, menu_class_name)

        cache.set(key, final_nodes, get_cms_setting('CACHE_DURATIONS')['menus'])
        # We need to have a list of the cache keys for languages and sites that
        # span several processes - so we follow the Django way and share through
        # the database. It's still cheaper than recomputing every time!
        # This way we can selectively invalidate per-site and per-language,
        # since the cache shared but the keys aren't
        CacheKey.objects.get_or_create(key=key, language=lang, site=site_id)
        return final_nodes

    def _mark_selected(self, nodes):
        # There /may/ be two nodes that get marked with selected. A published
        # and a draft version of the node. We'll mark both, later, the unused
        # one will be removed anyway.
        sel = []
        for node in nodes:
            node.sibling = False
            node.ancestor = False
            node.descendant = False
            node_abs_url = node.get_absolute_url()
            if node_abs_url == self.request.path[:len(node_abs_url)]:
                if sel:
                    if len(node_abs_url) > len(sel[0].get_absolute_url()):
                        sel = [node]
                    elif len(node_abs_url) == len(sel[0].get_absolute_url()):
                        sel.append(node)
                else:
                    sel = [node]
        for node in nodes:
            node.selected = (node in sel)
        return nodes

    def apply_modifiers(self, nodes, namespace=None, root_id=None,
            post_cut=False, breadcrumb=False):
        if not post_cut:
            nodes = self._mark_selected(nodes)

        # Only fetch modifiers when they're needed.
        # We can do this because unlike menu classes,
        # modifiers can't change on a request basis.
        for cls in self.pool.get_registered_modifiers():
            inst = cls(renderer=self)
            nodes = inst.modify(
                self.request, nodes, namespace, root_id, post_cut, breadcrumb)
        return nodes

    def get_nodes(self, namespace=None, root_id=None, site_id=None, breadcrumb=False):
        if not site_id:
            site_id = Site.objects.get_current().pk
        nodes = self._build_nodes(site_id)
        nodes = copy.deepcopy(nodes)
        nodes = self.apply_modifiers(
            nodes=nodes,
            namespace=namespace,
            root_id=root_id,
            post_cut=False,
            breadcrumb=breadcrumb,
        )
        return nodes

    def get_menu(self, menu_name):
        MenuClass = self.menus[menu_name]
        return MenuClass(renderer=self)


class MenuPool(object):

    def __init__(self):
        self.menus = {}
        self.modifiers = []
        self.discovered = False

    def get_renderer(self, request):
        self.discover_menus()
        # Returns a menu pool wrapper that is bound
        # to the given request and can perform
        # operations based on the given request.
        return MenuRenderer(pool=self, request=request)

    def discover_menus(self):
        if self.discovered:
            return
        # FIXME: Remove in 3.4
        load('menu')
        load('cms_menus')
        from menus.modifiers import register
        register()
        self.discovered = True

    def get_registered_menus(self, for_rendering=False):
        """
        Returns all registered menu classes.

        :param for_rendering: Flag that when True forces us to include
            all CMSAttachMenu subclasses, even if they're not attached.
        """
        self.discover_menus()
        registered_menus = {}

        for menu_class_name, menu_cls in self.menus.items():
            if isinstance(menu_cls, Menu):
                # A Menu **instance** was registered,
                # this is non-standard, but acceptable.
                menu_cls = menu_cls.__class__
            if hasattr(menu_cls, "get_instances"):
                # It quacks like a CMSAttachMenu.
                # Expand the one CMSAttachMenu into multiple classes.
                # Each class is bound to the instance the menu is attached to.
                _get_menu_class = partial(_get_menu_class_for_instance, menu_cls)

                instances = menu_cls.get_instances() or []
                for instance in instances:
                    # For each instance, we create a unique class
                    # that is bound to that instance.
                    # Doing this allows us to delay the instantiation
                    # of the menu class until it's needed.
                    # Plus we keep the menus consistent by always
                    # pointing to a class instead of an instance.
                    namespace = "{0}:{1}".format(
                        menu_class_name, instance.pk)
                    registered_menus[namespace] = _get_menu_class(instance)

                if not instances and not for_rendering:
                    # The menu is a CMSAttachMenu but has no instances,
                    # normally we'd just ignore it but it's been
                    # explicitly set that we are not rendering these menus
                    # via the (for_rendering) flag.
                    registered_menus[menu_class_name] = menu_cls
            elif hasattr(menu_cls, "get_nodes"):
                # This is another type of Menu, cannot be expanded, but must be
                # instantiated, none-the-less.
                registered_menus[menu_class_name] = menu_cls
            else:
                raise ValidationError(
                    "Something was registered as a menu, but isn't.")
        return registered_menus

    def get_registered_modifiers(self):
        return self.modifiers

    def clear(self, site_id=None, language=None, all=False):
        '''
        This invalidates the cache for a given menu (site_id and language)
        '''
        if all:
            cache_keys = CacheKey.objects.get_keys()
        else:
            cache_keys = CacheKey.objects.get_keys(site_id, language)
        to_be_deleted = cache_keys.distinct().values_list('key', flat=True)
        if to_be_deleted:
            cache.delete_many(to_be_deleted)
            cache_keys.delete()

    def register_menu(self, menu_cls):
        import warnings

        if menu_cls.__module__.split('.')[-1] == 'menu':
            warnings.warn('menu.py filename is deprecated, '
                          'and it will be removed in version 3.4; '
                          'please rename it to cms_menus.py', DeprecationWarning)
        from menus.base import Menu
        assert issubclass(menu_cls, Menu)
        if menu_cls.__name__ in self.menus:
            raise NamespaceAlreadyRegistered(
                "[{0}] a menu with this name is already registered".format(
                    menu_cls.__name__))
        # Note: menu_cls should still be the menu CLASS at this point.
        self.menus[menu_cls.__name__] = menu_cls

    def register_modifier(self, modifier_class):
        import os
        import inspect
        import warnings
        source_file = os.path.basename(inspect.stack()[1][1])
        if source_file == 'menu.py':
            warnings.warn('menu.py filename is deprecated, '
                          'and it will be removed in version 3.4; '
                          'please rename it to cms_menus.py', DeprecationWarning)
        from menus.base import Modifier
        assert issubclass(modifier_class, Modifier)
        if modifier_class not in self.modifiers:
            self.modifiers.append(modifier_class)

    def get_menus_by_attribute(self, name, value):
        """
        Returns the list of menus that match the name/value criteria provided.
        """
        # Note that we are limiting the output to only single instances of any
        # specific menu class. This is to address issue (#4041) which has
        # cropped-up in 3.0.13/3.0.0.
        # By setting for_rendering to False
        # we're limiting the output to menus
        # that are registered and have instances
        # (in case of attached menus).
        menus = self.get_registered_menus(for_rendering=False)
        return sorted(list(set([(menu.__name__, menu.name)
                                for menu_class_name, menu in menus.items()
                                if getattr(menu, name, None) == value])))

    def get_nodes_by_attribute(self, nodes, name, value):
        return [node for node in nodes if node.attr.get(name, None) == value]

    def apply_modifiers(self, nodes, request, namespace=None, root_id=None,
            post_cut=False, breadcrumb=False):
        warnings.warn('menu_pool.apply_modifiers is deprecated '
                      'and it will be removed in version 3.4; '
                      'please use the menu renderer instead.', DeprecationWarning)
        renderer = self.get_renderer(request)
        nodes = renderer.apply_modifiers(
            nodes=nodes,
            namespace=namespace,
            root_id=root_id,
            post_cut=post_cut,
            breadcrumb=breadcrumb,
        )
        return nodes

    def get_nodes(self, request, namespace=None, root_id=None, site_id=None,
                  breadcrumb=False):
        warnings.warn('menu_pool.get_nodes is deprecated '
                      'and it will be removed in version 3.4; '
                      'please use the menu renderer instead.', DeprecationWarning)
        renderer = self.get_renderer(request)
        nodes = renderer.get_nodes(
            namespace=namespace,
            root_id=root_id,
            site_id=site_id,
            breadcrumb=breadcrumb,
        )
        return nodes


menu_pool = MenuPool()
