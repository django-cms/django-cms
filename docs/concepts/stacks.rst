.. _stacks-reference:

#################################################
Displaying the same content on multiple locations
#################################################

If you need to display the same content on multiple locations you can use stacks.

Stacks have a name and a placeholder attached to them. There are 3 ways to use stacks.

1. stack templatetag

    You can use a template tag to display a placeholder in a template without the need for an
    actual placeholder on you models. This can be useful for:

    - Footer
    - Logo
    - Header
    - Text or content inside you app
    - Text or content inside of 3th party apps.

    Example:

        {% load stack_tags %}
        {% stack "footer" %}

    .. note::

        It is recommended to use stacks in your apphook apps instead of show_placeholder templatetags

2. stack plugins

    You can create a stack out of plugins. You can create stacks out of plugin trees. After you created
    a stack this way you can insert a stack plugin and select a stack to be displayed instead of the stack
    plugin.

3. stacks as templates

    If you create stacks out of plugin tree you can paste the plugins contained in a stack as template.
    For example you can create a teaser plugin tree out of a multicolumn, text and picture plugin.
    You can then paste this template at the appropriate place and just edit the plugins instead of creating
    the same structure over and over.



