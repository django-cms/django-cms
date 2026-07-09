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
                self.stdout.write('{}[instance: {}] ({})\n'.format(
                    apphook, attributes[1], '/'.join(attributes[0])
                ))
            else:
                self.stdout.write('{} ({})\n'.format(
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
    plugin_types = list(
        CMSPlugin.objects.order_by('plugin_type')
        .values_list('plugin_type', flat=True)
        .distinct()
    )

    for plugin_type in plugin_types:
        # get all plugins of this type
        plugins = CMSPlugin.objects.filter(plugin_type=plugin_type)
        plugin = {
            'type': plugin_type,
            'instances': plugins,
        }

        try:
            # does this plugin have a model? report unsaved instances
            model = plugin_pool.get_plugin(name=plugin_type).model
        # catch uninstalled plugins
        except KeyError:
            plugin['model'] = None
            plugin['unsaved_instances'] = []
            plugin_report.append(plugin)
            continue

        plugin['model'] = model

        if model._meta.concrete_model == CMSPlugin._meta.concrete_model:
            # Model-less plugin: the bound instance is the CMSPlugin row
            # itself, so there can never be unsaved instances.
            plugin['unsaved_instances'] = []
        else:
            # An instance is "unsaved" when its CMSPlugin row has no matching
            # row in the plugin's own (child) table. Resolve this with a single
            # bulk query for the saved ids instead of one query per instance.
            saved_ids = set(
                model.objects.filter(cmsplugin_ptr__in=plugins)
                .values_list('cmsplugin_ptr_id', flat=True)
            )
            plugin['unsaved_instances'] = [
                instance for instance in plugins if instance.pk not in saved_ids
            ]

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
                self.stdout.write(f'  model      : {plugin_model.__module__}.{plugin_model.__name__}  \n')
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
