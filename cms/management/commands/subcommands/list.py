from cms.models import Page
from cms.models.pluginmodel import CMSPlugin
from cms.plugin_pool import plugin_pool

from .base import SubcommandsCommand


class ListApphooksCommand(SubcommandsCommand):
    help_string = 'Lists all apphooks in pages'
    command_name = 'apphooks'

    def handle(self, *args, **options):
        urls = list(
            Page.objects.exclude(application_urls='').exclude(
                application_urls__isnull=True
            ).values_list(
                'application_urls', 'application_namespace'
            )
        )
        apphooks = {}
        for apphook, application_namespace in urls:
            if apphook in apphooks:
                apphooks[apphook][0].append('active')
            else:
                apphooks[apphook] = [['active'], application_namespace]
        for apphook, attributes in apphooks.items():
            attributes[0].sort()
            if attributes[1]:
                self.stdout.write('{0}[instance: {1}] ({2})\n'.format(
                    apphook, attributes[1], '/'.join(attributes[0])
                ))
            else:
                self.stdout.write('{0} ({1})\n'.format(
                    apphook, '/'.join(attributes[0])
                ))


def plugin_report():
    """
    Returns a report of existing plugins

    structure of report:
    [
        {
            'type': CMSPlugin class,
            'model': plugin_type.model,
            'instances': instances in the CMSPlugin table,
            'unsaved_instances': those with no corresponding model instance,
        },
    ]
    """
    plugin_report = []
    all_plugins = CMSPlugin.objects.order_by('plugin_type')
    plugin_types = list(set(all_plugins.values_list('plugin_type', flat=True)))
    plugin_types.sort()

    for plugin_type in plugin_types:
        plugin = {}
        plugin['type'] = plugin_type
        try:
            # get all plugins of this type
            plugins = CMSPlugin.objects.filter(plugin_type=plugin_type)
            plugin['instances'] = plugins
            # does this plugin have a model? report unsaved instances
            plugin['model'] = plugin_pool.get_plugin(name=plugin_type).model
            unsaved_instances = [p for p in plugins if not p.get_plugin_instance()[0]]
            plugin['unsaved_instances'] = unsaved_instances

        # catch uninstalled plugins
        except KeyError:
            plugin['model'] = None
            plugin['instances'] = plugins
            plugin['unsaved_instances'] = []

        plugin_report.append(plugin)

    return plugin_report


class ListPluginsCommand(SubcommandsCommand):
    help_string = 'Lists all plugins in CMSPlugin'
    command_name = 'plugins'

    def handle(self, *args, **options):
        self.stdout.write('==== Plugin report ==== \n\n')
        self.stdout.write('There are %s plugin types in your database \n' % len(plugin_report()))
        for plugin in plugin_report():
            self.stdout.write('\n%s \n' % plugin['type'])

            plugin_model = plugin['model']
            instances = len(plugin['instances'])
            unsaved_instances = len(plugin['unsaved_instances'])

            if not plugin_model:
                self.stdout.write(self.style.ERROR('  ERROR      : not installed \n'))

            elif plugin_model == CMSPlugin:
                self.stdout.write('    model-less plugin \n')
                self.stdout.write('    unsaved instance(s) : %s  \n' % unsaved_instances)

            else:
                self.stdout.write('  model      : %s.%s  \n' % (plugin_model.__module__, plugin_model.__name__))
                if unsaved_instances:
                    self.stdout.write(self.style.ERROR('  ERROR      : %s unsaved instance(s) \n' % unsaved_instances))

            self.stdout.write('  instance(s): %s \n' % instances)


class ListCommand(SubcommandsCommand):
    help_string = 'List objects of the following types:'
    command_name = 'list'
    subcommands = {
        'apphooks': ListApphooksCommand,
        'plugins': ListPluginsCommand
    }
