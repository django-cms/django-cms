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
        model_less_instances = []
        unsaved_instances = []
        self.stdout.write("... deleting orphaned plugins\n")        
        for plugin in report:
            # delete items with no model
            if not plugin["model"]:
                for instance in plugin["instances"]:
                    model_less_instances.append(instance)
                    instance.delete()
                    
            # delete items with unsaved instances
            for instance in plugin["unsaved_instances"]:
                unsaved_instances.append(instance)
                instance.delete()
        self.stdout.write("Deleted %s model-less plugins and %s plugins with unsaved instances\n" % (len(model_less_instances), len(unsaved_instances)))
        self.stdout.write("all done\n")
                                    