from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Exists, OuterRef

from cms.management.commands.subcommands.list import plugin_report
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin

from .base import SubcommandsCommand


class DeleteOrphanedPluginsCommand(SubcommandsCommand):
    help_string = (
        'Delete plugins from the CMSPlugins table that should have instances '
        'but don\'t, and ones for which a corresponding plugin model can no '
        'longer be found. ATTENTION: Also removes plugins of apps currently not present in INSTALLED_APPS. '
        'Ensure nothing is temporarily commented out.'
    )
    command_name = 'delete-orphaned-plugins'

    def get_detached_placeholders(self):
        detached_placeholder_ids = []
        content_types = list(
            Placeholder.objects.exclude(content_type_id__isnull=True)
            .values_list('content_type_id', flat=True)
            .distinct()
        )
        content_type_map = ContentType.objects.in_bulk(content_types)

        for content_type_id in content_types:
            content_type = content_type_map.get(content_type_id)
            model_class = content_type.model_class() if content_type else None

            if model_class is None:
                detached_placeholder_ids.extend(
                    Placeholder.objects.filter(content_type_id=content_type_id)
                    .values_list('id', flat=True)
                )
                continue

            detached_placeholder_ids.extend(
                Placeholder.objects.filter(
                    content_type_id=content_type_id,
                    object_id__isnull=False,
                )
                .annotate(
                    object_exists=Exists(
                        model_class._base_manager.filter(pk=OuterRef('object_id'))
                    )
                )
                .filter(object_exists=False)
                .values_list('id', flat=True)
            )
        return detached_placeholder_ids

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

        detached_placeholder_ids = self.get_detached_placeholders()

        if options.get('interactive'):
            confirm = input("""
You have requested to delete any instances of uninstalled plugins and empty plugin instances.
There are %d uninstalled plugins, %d empty plugins, and %d detached placeholders.
Are you sure you want to do this?
Type 'yes' to continue, or 'no' to cancel: """ % (len(uninstalled_instance_ids), len(unsaved_instance_ids), len(detached_placeholder_ids)))
        else:
            confirm = 'yes'

        if confirm == 'yes':
            # delete items whose plugin is uninstalled and items with unsaved instances
            self.stdout.write('... deleting any instances of uninstalled plugins, empty plugin instances, and detached placeholders\n')

            with transaction.atomic():
                if detached_placeholder_ids:
                    Placeholder.objects.filter(id__in=detached_placeholder_ids).delete()

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
                f'Deleted instances of: \n    {len(uninstalled_instance_ids)} uninstalled plugins  \n    {len(unsaved_instance_ids)} plugins with unsaved instances\n    {len(detached_placeholder_ids)} detached placeholders\n'
            )
            self.stdout.write('all done\n')
