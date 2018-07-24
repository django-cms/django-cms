from django.db import migrations

try:
    IrreversibleError = migrations.Migration.IrreversibleError
except AttributeError:
    from django.db.migrations.exceptions import IrreversibleError


class IrreversibleMigration(migrations.Migration):

    def unapply(self, project_state, schema_editor, collect_sql=False):
        raise IrreversibleError('Migration %s is not reversible' % self.name)
