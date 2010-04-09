from django.contrib.sites.models import Site
from cms.templatetags.cms_tags import PlaceholderNode
from django.template.loader import get_template
from django.template.loader_tags import ConstantIncludeNode, ExtendsNode, BlockNode
from django.template import NodeList, TextNode, VariableNode

def _extend_blocks(extend_node, blocks):
    """
    Extends the dictionary `blocks` with *new* blocks in the parent node (recursive)
    """
    # we don't support variable extensions
    if extend_node.parent_name_expr:
        return
    parent = extend_node.get_parent(None)
    # Search for new blocks
    for node in parent.nodelist.get_nodes_by_type(BlockNode):
        if not node.name in blocks:
            blocks[node.name] = node
        else:
            # set this node as the super node (for {{ block.super }})
            blocks[node.name].super = node
    # search for further ExtendsNodes
    for node in parent.nodelist:
        if not isinstance(node, TextNode):
            if isinstance(node, ExtendsNode):
                _extend_blocks(node, blocks)
            break

def _extend_nodelist(extend_node):
    """
    Returns a list of placeholders found in the parent template(s) of this
    ExtendsNode
    """
    # we don't support variable extensions
    if extend_node.parent_name_expr:
        return []
    blocks = extend_node.blocks
    _extend_blocks(extend_node, blocks)
    placeholders = []
    for block in blocks.values():
        placeholders += _scan_placeholders(block.nodelist, block)
    return placeholders

def _scan_placeholders(nodelist, current_block=None):
    placeholders = []

    for node in nodelist:
        # check if this is a placeholder first
        if isinstance(node, PlaceholderNode):
            placeholders.append(node.name)
        # if it's a Constant Include Node ({% include "template_name.html" %})
        # scan the child template
        elif isinstance(node, ConstantIncludeNode):
            placeholders += _scan_placeholders(node.template.nodelist, current_block)
        # handle {% extends ... %} tags
        elif isinstance(node, ExtendsNode):
            placeholders += _extend_nodelist(node)
        # in block nodes we have to scan for super blocks
        elif isinstance(node, VariableNode) and current_block:
            if node.filter_expression.token == 'block.super':
                placeholders += _scan_placeholders(current_block.super.nodelist, current_block.super)
        # if the node has the newly introduced 'child_nodelists' attribute, scan
        # those attributes for nodelists and recurse them
        elif hasattr(node, 'child_nodelists'):
            for nodelist_name in node.child_nodelists:
                if hasattr(node, nodelist_name):
                    subnodelist = getattr(node, nodelist_name)
                    if isinstance(subnodelist, NodeList):
                        if isinstance(node, BlockNode):
                            current_block = node
                        placeholders += _scan_placeholders(subnodelist, current_block)
        # else just scan the node for nodelist instance attributes
        else:
            for attr in dir(node):
                obj = getattr(node, attr)
                if isinstance(obj, NodeList):
                    if isinstance(node, BlockNode):
                        current_block = node
                    placeholders += _scan_placeholders(obj, current_block)
    return placeholders

def get_placeholders(template):
     compiled_template = get_template(template)
     placeholders = _scan_placeholders(compiled_template.nodelist)
     return placeholders

SITE_VAR = "site__exact"

def current_site(request):
    if SITE_VAR in request.REQUEST:
        return Site.objects.get(pk=request.REQUEST[SITE_VAR])
    else:
        site_pk = request.session.get('cms_admin_site', None)
        if site_pk:
            try:
                return Site.objects.get(pk=site_pk)
            except Site.DoesNotExist:
                return None
        else:
            return Site.objects.get_current()