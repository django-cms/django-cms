from cms.models import CMSPlugin


class MultiColumns(CMSPlugin):
    """
    A plugin that has sub Column classes
    """

    def __str__(self):
        plugins = self.child_plugin_instances or []
        return f"{len(plugins)} columns"
