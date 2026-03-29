from cms.management.commands.subcommands.list import plugin_report
from cms.models.pluginmodel import CMSPlugin

from .base import SubcommandsCommand


class DeleteOrphanedPluginsCommand(SubcommandsCommand):
    help_string = ('Delete plugins from the CMSPlugins table that should have instances '
                   'but don\'t, and ones for which a corresponding plugin model can no '
                   'longer be found')
    command_name = 'delete-orphaned-plugins'

    def handle(self, *args, **options):
        """
        Obtains a plugin report -
        cms.management.commands.subcommands.list.plugin_report - and uses it
        to delete orphaned plugins from the database, i.e. ones that are no
        longer installed, and ones that have no corresponding saved plugin
        instances (as will happen if a plugin is inserted into a placeholder,
        but not saved).
        """
        self.stdout.write('Obtaining plugin report\n')
        uninstalled_instance_ids = []
        unsaved_instance_ids = []

        for plugin in plugin_report():
            if not plugin['model']:
                for instance in plugin['instances']:
                    uninstalled_instance_ids.append(instance.pk)

            for instance in plugin['unsaved_instances']:
                unsaved_instance_ids.append(instance.pk)

        if options.get('interactive'):
            confirm = input("""
You have requested to delete any instances of uninstalled plugins and empty plugin instances.
There are %d uninstalled plugins and %d empty plugins.
Are you sure you want to do this?
Type 'yes' to continue, or 'no' to cancel: """ % (len(uninstalled_instance_ids), len(unsaved_instance_ids)))
        else:
            confirm = 'yes'

        if confirm == 'yes':
            # delete items whose plugin is uninstalled and items with unsaved instances
            self.stdout.write('... deleting any instances of uninstalled plugins and empty plugin instances\n')

            for instance_id in uninstalled_instance_ids:
                try:
                    instance = CMSPlugin.objects.get(pk=instance_id)
                except CMSPlugin.DoesNotExist:
                    continue

                if instance.placeholder:
                    instance.placeholder.delete_plugin(instance)
                else:
                    instance.delete()

            for instance_id in unsaved_instance_ids:
                try:
                    instance = CMSPlugin.objects.get(pk=instance_id)
                except CMSPlugin.DoesNotExist:
                    continue

                if instance.placeholder:
                    instance.placeholder.delete_plugin(instance)
                else:
                    instance.delete()

            self.stdout.write(
                f'Deleted instances of: \n    {len(uninstalled_instance_ids)} uninstalled plugins  \n    {len(unsaved_instance_ids)} plugins with unsaved instances\n'
            )
            self.stdout.write('all done\n')
