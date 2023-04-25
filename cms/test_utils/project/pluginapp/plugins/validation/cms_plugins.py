from cms.plugin_base import CMSPluginBase


class NonExisitngRenderTemplate(CMSPluginBase):
    name = 'SubTest'
    module = 'Test'
    render_template = 'i_do_not_exist.html'
    allow_children = True


class NoSubPluginRender(CMSPluginBase):
    name = 'SubSubTest'
    module = 'Test'
    render_template = 'plugins/sub_empty_plugin.html'
    allow_children = True


class NoRender(CMSPluginBase):
    name = 'norender'


class NoRenderButChildren(CMSPluginBase):
    name = 'norender2'
    render_plugin = False
    allow_children = True


class DynTemplate(CMSPluginBase):
    name = 'norender3'
    render_plugin = True

    def get_render_template(self):
        raise KeyError('asd')

    render_template = property(get_render_template)
