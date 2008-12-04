from django.db import connection

from common import BaseEvolutionOperations

class EvolutionOperations(BaseEvolutionOperations):
    def rename_column(self, opts, old_field, new_field):
        if old_field.column == new_field.column:
            # No Operation
            return []
    
        qn = connection.ops.quote_name
        params = (qn(opts.db_table), qn(old_field.column), qn(new_field.column))
        return ['ALTER TABLE %s RENAME COLUMN %s TO %s;' % params]
    