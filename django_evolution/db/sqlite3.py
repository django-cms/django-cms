from django.core.management import color
from django.db import connection, models

from common import BaseEvolutionOperations

TEMP_TABLE_NAME = 'TEMP_TABLE'

class EvolutionOperations(BaseEvolutionOperations):
    def delete_column(self, model, f):
        qn = connection.ops.quote_name
        output = []
    
        field_list = [field for field in model._meta.local_fields
                        if f.name != field.name # Remove the field to be deleted
                        and field.db_type() is not None] # and any Generic fields
        table_name = model._meta.db_table
    
        output.extend(self.create_temp_table(field_list))
        output.extend(self.copy_to_temp_table(table_name, field_list))
        output.extend(self.delete_table(table_name))
        output.extend(self.create_table(table_name, field_list))
        output.extend(self.copy_from_temp_table(table_name, field_list))
        output.extend(self.delete_table(TEMP_TABLE_NAME))
    
        return output
    
    def create_mock_model(self, model, fields):
        field_sig_dict = {}
        for f in fields:
            field_sig_dict[f.name] = create_field_sig(field)
    
        proj_sig = create_project_sig()
        model_sig = create_model_sig(model)
        model_sig['fields'] = field_sig_dict
        mock_model = MockModel(proj_sig, model.app_name, model.model_name, model_sig, stub=False)
        
    def copy_to_temp_table(self, source_table_name, field_list):
        qn = connection.ops.quote_name
        output = [self.create_temp_table(field_list)]
        columns = []
        for field in field_list:
            if not models.ManyToManyField == field.__class__:
                columns.append(qn(field.column))
        column_names = ', '.join(columns)
        return ['INSERT INTO %s SELECT %s FROM %s;' % (qn(TEMP_TABLE_NAME), column_names, qn(source_table_name))]
    
    def copy_from_temp_table(self, dest_table_name, field_list):
        qn = connection.ops.quote_name
        columns = []
        for field in field_list:
            if not models.ManyToManyField == field.__class__:
                columns.append(qn(field.column))
        column_names = ', '.join(columns)
        params = {
            'dest_table_name': qn(dest_table_name),
            'temp_table': qn(TEMP_TABLE_NAME),
            'column_names': column_names,
        }
    
        return ['INSERT INTO %(dest_table_name)s (%(column_names)s) SELECT %(column_names)s FROM %(temp_table)s;' % params]
    
    def insert_to_temp_table(self, field, initial):
        qn = connection.ops.quote_name
    
        # At this point, initial can only be None if null=True, otherwise it is 
        # a user callable or the default AddFieldInitialCallback which will shortly raise an exception.
        if initial is None:
            return []

        params = {
            'table_name': qn(TEMP_TABLE_NAME),
            'column_name': qn(field.column),
        }

        if callable(initial):
            params['value'] = initial()
            return ["UPDATE %(table_name)s SET %(column_name)s = %(value)s;" % params]
        else:
            return [("UPDATE %(table_name)s SET %(column_name)s = %%s;" % params, (initial,))]
        

    def create_temp_table(self, field_list):
        return self.create_table(TEMP_TABLE_NAME, field_list, True, False)

    def create_indexes_for_table(self, table_name, field_list):
        class FakeMeta(object):
            def __init__(self, table_name, field_list):
                self.db_table = table_name
                self.local_fields = field_list
                self.fields = field_list # Required for Pre QS-RF support
                self.db_tablespace = None

        class FakeModel(object):
            def __init__(self, table_name, field_list):
                self._meta = FakeMeta(table_name, field_list)

        style = color.no_style()
        return connection.creation.sql_indexes_for_model(FakeModel(table_name, field_list), style)
    
    def create_table(self, table_name, field_list, temporary=False, create_index=True):
        qn = connection.ops.quote_name
        output = []
    
        create = ['CREATE']
        if temporary:
            create.append('TEMPORARY')
        create.append('TABLE %s' % qn(table_name))
        output = [' '.join(create)]
        output.append('(')
        columns = []
        for field in field_list:
            if not models.ManyToManyField == field.__class__:
                column_name = qn(field.column)
                column_type = field.db_type()
                params = [column_name, column_type]
                if field.null:
                    params.append('NULL')
                else:
                    params.append('NOT NULL')
                if field.unique:
                    params.append('UNIQUE')
                if field.primary_key:
                    params.append('PRIMARY KEY')
                columns.append(' '.join(params))

        output.append(', '.join(columns))
        output.append(');')
        output = [''.join(output)]
    
        if create_index:
            output.extend(self.create_indexes_for_table(table_name, field_list))

        return output
    
    def rename_column(self, opts, old_field, new_field):
        if old_field.column == new_field.column:
            # No Operation
            return []

        original_fields = opts.local_fields
        new_fields = []
        for f in original_fields:
            if f.db_type() is not None: # Ignore Generic Fields
                if f.name == old_field.name:
                    new_fields.append(new_field)
                else:
                    new_fields.append(f)

        table_name = opts.db_table
        output = []
        output.extend(self.create_temp_table(new_fields))
        output.extend(self.copy_to_temp_table(table_name, original_fields))
        output.extend(self.delete_table(table_name))
        output.extend(self.create_table(table_name, new_fields))
        output.extend(self.copy_from_temp_table(table_name, new_fields))
        output.extend(self.delete_table(TEMP_TABLE_NAME))
    
        return output
    
    def add_column(self, model, f, initial):
        output = []
        table_name = model._meta.db_table
        original_fields = [field for field in model._meta.local_fields if field.db_type() is not None]
        new_fields = original_fields
        new_fields.append(f)
    
        output.extend(self.create_temp_table(new_fields))
        output.extend(self.copy_to_temp_table(table_name, original_fields))
        output.extend(self.insert_to_temp_table(f, initial))
        output.extend(self.delete_table(table_name))
        output.extend(self.create_table(table_name, new_fields, create_index=False))
        output.extend(self.copy_from_temp_table(table_name, new_fields))
        output.extend(self.delete_table(TEMP_TABLE_NAME))
        return output

    def change_null(self, model, field_name, new_null_attr, initial=None):
        return self.change_attribute(model, field_name, 'null', new_null_attr, initial)
        
    def change_max_length(self, model, field_name, new_max_length, initial=None):
        return self.change_attribute(model, field_name, 'max_length', new_max_length, initial)
        
    def change_unique(self, model, field_name, new_unique_value, initial=None):
        return self.change_attribute(model, field_name, '_unique', new_unique_value, initial)
        
    def change_attribute(self, model, field_name, attr_name, new_attr_value, initial=None):
        output = []
        opts = model._meta
        table_name = opts.db_table
        setattr(opts.get_field(field_name), attr_name, new_attr_value)
        fields = [f for f in opts.local_fields if f.db_type() is not None]
        
        output.extend(self.create_temp_table(fields))
        output.extend(self.copy_to_temp_table(table_name, fields))
        output.extend(self.insert_to_temp_table(opts.get_field(field_name), initial))
        output.extend(self.delete_table(table_name))
        output.extend(self.create_table(table_name, fields, create_index=False))
        output.extend(self.copy_from_temp_table(table_name, fields))
        output.extend(self.delete_table(TEMP_TABLE_NAME))
        return output
