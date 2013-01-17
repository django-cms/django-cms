from cms.models import Page, CMSPlugin
from django.core.management.base import NoArgsCommand
from cms.management.commands.subcommands.list import plugin_report


class DeleteOrphanedPluginsCommand(NoArgsCommand):
    help = "Delete plugins from the CMSPlugins table that should have instances but don't, and ones for which a corresponding plugin model can no longer be found"

    def handle_noargs(self, **options):
        """
        Obtains a plugin report -
        cms.management.commands.subcommands.list.plugin_report - and uses it
        to delete orphaned plugins from the database, i.e. ones that are no
        longer installed, and ones that have no corresponding saved plugin
        instances (as will happen if a plugin is inserted into a placeholder,
        but not saved).
        """
        self.stdout.write("Obtaining plugin report\n")
        report = plugin_report()
        uninstalled_instances = []
        unsaved_instances = []

        # delete items whose plugin is uninstalled and items with unsaved instances
        self.stdout.write("... deleting any instances of uninstalled plugins and unsaved plugin instances\n")        
        
        for plugin in report:
            if not plugin["model"]:
                for instance in plugin["instances"]:
                    uninstalled_instances.append(instance)
                    instance.delete()
                    
            for instance in plugin["unsaved_instances"]:
                unsaved_instances.append(instance)
                instance.delete()

        self.stdout.write("Deleted instances of: \n    %s uninstalled plugins  \n    %s plugins with unsaved instances\n" % (len(uninstalled_instances), len(unsaved_instances)))
        self.stdout.write("all done\n")
                                    