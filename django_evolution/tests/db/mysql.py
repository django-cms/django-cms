add_field = {
    'AddNonNullNonCallableColumnModel':
        '\n'.join([
            'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field` integer ;',
            'UPDATE `tests_testmodel` SET `added_field` = 1 WHERE `added_field` IS NULL;',
            'ALTER TABLE `tests_testmodel` MODIFY COLUMN `added_field` integer NOT NULL;',
        ]),
    'AddNonNullCallableColumnModel':
        '\n'.join([
            'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field` integer ;',
            'UPDATE `tests_testmodel` SET `added_field` = `int_field` WHERE `added_field` IS NULL;',
            'ALTER TABLE `tests_testmodel` MODIFY COLUMN `added_field` integer NOT NULL;',
        ]),
    'AddNullColumnWithInitialColumnModel':
        '\n'.join([
            'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field` integer ;',
            'UPDATE `tests_testmodel` SET `added_field` = 1 WHERE `added_field` IS NULL;',
        ]),
    'AddStringColumnModel':
        '\n'.join([
            'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field` varchar(10) ;',
            'UPDATE `tests_testmodel` SET `added_field` = \'abc\\\'s xyz\' WHERE `added_field` IS NULL;',
            'ALTER TABLE `tests_testmodel` MODIFY COLUMN `added_field` varchar(10) NOT NULL;',
        ]),
    'AddDateColumnModel':
        '\n'.join([
            'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field` datetime ;',
            'UPDATE `tests_testmodel` SET `added_field` = 2007-12-13 16:42:00 WHERE `added_field` IS NULL;',
            'ALTER TABLE `tests_testmodel` MODIFY COLUMN `added_field` datetime NOT NULL;',
        ]),    
    'AddDefaultColumnModel':
        '\n'.join([
            'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field` integer ;',
            'UPDATE `tests_testmodel` SET `added_field` = 42 WHERE `added_field` IS NULL;',
            'ALTER TABLE `tests_testmodel` MODIFY COLUMN `added_field` integer NOT NULL;',
        ]),
    'AddEmptyStringDefaultColumnModel':
        '\n'.join([
            'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field` varchar(20) ;',
            'UPDATE `tests_testmodel` SET `added_field` = \'\' WHERE `added_field` IS NULL;',
            'ALTER TABLE `tests_testmodel` MODIFY COLUMN `added_field` varchar(20) NOT NULL;',
        ]),
    'AddNullColumnModel': 
        'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field` integer NULL ;',
    'NonDefaultColumnModel': 
        'ALTER TABLE `tests_testmodel` ADD COLUMN `non-default_column` integer NULL ;',
    'AddColumnCustomTableModel':  
        'ALTER TABLE `custom_table_name` ADD COLUMN `added_field` integer NULL ;',
    'AddIndexedColumnModel': 
        '\n'.join([
            'ALTER TABLE `tests_testmodel` ADD COLUMN `add_field` integer NULL ;',
            'CREATE INDEX `tests_testmodel_add_field` ON `tests_testmodel` (`add_field`);'
        ]),
    'AddUniqueColumnModel': 
        'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field` integer NULL UNIQUE;',
    'AddUniqueIndexedModel': 
        'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field` integer NULL UNIQUE;',
    'AddForeignKeyModel': 
        '\n'.join([
            'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field_id` integer NULL REFERENCES `tests_addanchor1` (`id`) ;',
            'CREATE INDEX `tests_testmodel_added_field_id` ON `tests_testmodel` (`added_field_id`);'
        ]),
    'AddManyToManyDatabaseTableModel': 
        '\n'.join([
            'CREATE TABLE `tests_testmodel_added_field` (',
            '    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,',
            '    `testmodel_id` integer NOT NULL,',
            '    `addanchor1_id` integer NOT NULL,',
            '    UNIQUE (`testmodel_id`, `addanchor1_id`)',
            ')',
            ';',
            'ALTER TABLE `tests_testmodel_added_field` ADD CONSTRAINT testmodel_id_refs_id_12ea61cd FOREIGN KEY (`testmodel_id`) REFERENCES `tests_testmodel` (`id`);',
            'ALTER TABLE `tests_testmodel_added_field` ADD CONSTRAINT addanchor1_id_refs_id_7efbb240 FOREIGN KEY (`addanchor1_id`) REFERENCES `tests_addanchor1` (`id`);'            
        ]),
     'AddManyToManyNonDefaultDatabaseTableModel': 
        '\n'.join([
            'CREATE TABLE `tests_testmodel_added_field` (',
            '    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,',
            '    `testmodel_id` integer NOT NULL,',
            '    `addanchor2_id` integer NOT NULL,',
            '    UNIQUE (`testmodel_id`, `addanchor2_id`)',
            ')',
            ';',
            'ALTER TABLE `tests_testmodel_added_field` ADD CONSTRAINT testmodel_id_refs_id_12ea61cd FOREIGN KEY (`testmodel_id`) REFERENCES `tests_testmodel` (`id`);',
            'ALTER TABLE `tests_testmodel_added_field` ADD CONSTRAINT addanchor2_id_refs_id_13c1da78 FOREIGN KEY (`addanchor2_id`) REFERENCES `custom_add_anchor_table` (`id`);'
        ]),
     'AddManyToManySelf': 
        '\n'.join([
            'CREATE TABLE `tests_testmodel_added_field` (',
            '    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,',
            '    `from_testmodel_id` integer NOT NULL,',
            '    `to_testmodel_id` integer NOT NULL,',
            '    UNIQUE (`from_testmodel_id`, `to_testmodel_id`)',
            ')',
            ';',
            'ALTER TABLE `tests_testmodel_added_field` ADD CONSTRAINT from_testmodel_id_refs_id_12ea61cd FOREIGN KEY (`from_testmodel_id`) REFERENCES `tests_testmodel` (`id`);',
            'ALTER TABLE `tests_testmodel_added_field` ADD CONSTRAINT to_testmodel_id_refs_id_12ea61cd FOREIGN KEY (`to_testmodel_id`) REFERENCES `tests_testmodel` (`id`);'
        ]),
}

delete_field = {
    'DefaultNamedColumnModel': 
        'ALTER TABLE `tests_testmodel` DROP COLUMN `int_field` CASCADE;',
    'NonDefaultNamedColumnModel': 
        'ALTER TABLE `tests_testmodel` DROP COLUMN `non-default_db_column` CASCADE;',
    'ConstrainedColumnModel': 
        'ALTER TABLE `tests_testmodel` DROP COLUMN `int_field3` CASCADE;',
    'DefaultManyToManyModel': 
        'DROP TABLE `tests_testmodel_m2m_field1`;',
    'NonDefaultManyToManyModel': 
        'DROP TABLE `non-default_m2m_table`;',
    'DeleteForeignKeyModel': 
        'ALTER TABLE `tests_testmodel` DROP COLUMN `fk_field1_id` CASCADE;',
    'DeleteColumnCustomTableModel': 
        'ALTER TABLE `custom_table_name` DROP COLUMN `value` CASCADE;',
}

change_field = {
    "SetNotNullChangeModelWithConstant":
        '\n'.join([
            'UPDATE `tests_testmodel` SET `char_field1` = \'abc\\\'s xyz\' WHERE `char_field1` IS NULL;',
            'ALTER TABLE `tests_testmodel` MODIFY COLUMN `char_field1` varchar(25) NOT NULL;',
        ]),
    "SetNotNullChangeModelWithCallable":
            '\n'.join([
                'UPDATE `tests_testmodel` SET `char_field1` = `char_field` WHERE `char_field1` IS NULL;',
                'ALTER TABLE `tests_testmodel` MODIFY COLUMN `char_field1` varchar(25) NOT NULL;',
            ]),
    "SetNullChangeModel": 'ALTER TABLE `tests_testmodel` MODIFY COLUMN `char_field2` varchar(30) DEFAULT NULL;',
    "NoOpChangeModel": '',
    'IncreasingMaxLengthChangeModel':
            '\n'.join([
                'UPDATE `tests_testmodel` SET `char_field`=LEFT(`char_field`,45);',
                'ALTER TABLE `tests_testmodel` MODIFY COLUMN `char_field` varchar(45);',
            ]),
    'DecreasingMaxLengthChangeModel':  
            '\n'.join([
                'UPDATE `tests_testmodel` SET `char_field`=LEFT(`char_field`,1);',
                'ALTER TABLE `tests_testmodel` MODIFY COLUMN `char_field` varchar(1);',
            ]),
    "DBColumnChangeModel": 'ALTER TABLE `tests_testmodel` CHANGE COLUMN `custom_db_column` `customised_db_column` integer NOT NULL;',
    "M2MDBTableChangeModel": 'RENAME TABLE `change_field_non-default_m2m_table` TO `custom_m2m_db_table_name`;',
    "AddDBIndexChangeModel": 'CREATE INDEX `tests_testmodel_int_field2` ON `tests_testmodel` (`int_field2`);',
    "RemoveDBIndexChangeModel": 'DROP INDEX `tests_testmodel_int_field1` ON `tests_testmodel`;',
    "AddUniqueChangeModel": 'CREATE UNIQUE INDEX int_field4 ON `tests_testmodel`(`int_field4`);',
    "RemoveUniqueChangeModel": 'DROP INDEX int_field3 ON `tests_testmodel`;',
    "MultiAttrChangeModel": 
        '\n'.join([
            'ALTER TABLE `tests_testmodel` MODIFY COLUMN `char_field2` varchar(30) DEFAULT NULL;',
            'ALTER TABLE `tests_testmodel` CHANGE COLUMN `custom_db_column` `custom_db_column2` integer NOT NULL;',
            'UPDATE `tests_testmodel` SET `char_field`=LEFT(`char_field`,35);',
            'ALTER TABLE `tests_testmodel` MODIFY COLUMN `char_field` varchar(35);',
        ]),
    "MultiAttrSingleFieldChangeModel": 
        '\n'.join([
            'UPDATE `tests_testmodel` SET `char_field2`=LEFT(`char_field2`,35);',
            'ALTER TABLE `tests_testmodel` MODIFY COLUMN `char_field2` varchar(35);',
            'ALTER TABLE `tests_testmodel` MODIFY COLUMN `char_field2` varchar(35) DEFAULT NULL;',
        ]),
    "RedundantAttrsChangeModel":
        '\n'.join([
            'ALTER TABLE `tests_testmodel` MODIFY COLUMN `char_field2` varchar(30) DEFAULT NULL;',
            'ALTER TABLE `tests_testmodel` CHANGE COLUMN `custom_db_column` `custom_db_column3` integer NOT NULL;',
            'UPDATE `tests_testmodel` SET `char_field`=LEFT(`char_field`,35);',
            'ALTER TABLE `tests_testmodel` MODIFY COLUMN `char_field` varchar(35);',
        ]),
}

delete_model = {
    'BasicModel': 
        'DROP TABLE `tests_basicmodel`;',
    'BasicWithM2MModel': 
        '\n'.join([
            'DROP TABLE `tests_basicwithm2mmodel_m2m`;',
            'DROP TABLE `tests_basicwithm2mmodel`;'
        ]),
    'CustomTableModel': 
        'DROP TABLE `custom_table_name`;',
    'CustomTableWithM2MModel': 
        '\n'.join([
            'DROP TABLE `another_custom_table_name_m2m`;',
            'DROP TABLE `another_custom_table_name`;'
        ]),
}

delete_application = {
    'DeleteApplication':
        '\n'.join([
            'DROP TABLE `tests_appdeleteanchor1`;',
            'DROP TABLE `tests_testmodel_anchor_m2m`;',
            'DROP TABLE `tests_testmodel`;',
            'DROP TABLE `app_delete_custom_add_anchor_table`;',
            'DROP TABLE `app_delete_custom_table_name`;',
        ]),
}

rename_field = {
    'RenameColumnModel': 
        'ALTER TABLE `tests_testmodel` CHANGE COLUMN `int_field` `renamed_field` integer NOT NULL;',
    'RenameColumnWithTableNameModel': 
        'ALTER TABLE `tests_testmodel` CHANGE COLUMN `int_field` `renamed_field` integer NOT NULL;',
    'RenamePrimaryKeyColumnModel': 
        'ALTER TABLE `tests_testmodel` CHANGE COLUMN `id` `my_pk_id`;',
    'RenameForeignKeyColumnModel': 
        'ALTER TABLE `tests_testmodel` CHANGE COLUMN `fk_field_id` `renamed_field_id` integer NOT NULL;',
    'RenameNonDefaultColumnNameModel': 
        'ALTER TABLE `tests_testmodel` CHANGE COLUMN `custom_db_col_name` `renamed_field` integer NOT NULL;',
    'RenameNonDefaultColumnNameToNonDefaultNameModel': 
        'ALTER TABLE `tests_testmodel` CHANGE COLUMN `custom_db_col_name` `non-default_column_name` integer NOT NULL;',
    'RenameNonDefaultColumnNameToNonDefaultNameAndTableModel': 
        'ALTER TABLE `tests_testmodel` CHANGE COLUMN `custom_db_col_name` `non-default_column_name2` integer NOT NULL;',
    'RenameColumnCustomTableModel': 
        'ALTER TABLE `custom_rename_table_name` CHANGE COLUMN `value` `renamed_field` integer NOT NULL;',
    'RenameManyToManyTableModel': 
        'ALTER TABLE `tests_testmodel_m2m_field` RENAME TO `tests_testmodel_renamed_field`;',
    'RenameManyToManyTableWithColumnNameModel': 
        'ALTER TABLE `tests_testmodel_m2m_field` RENAME TO `tests_testmodel_renamed_field`;',
    'RenameNonDefaultManyToManyTableModel': 
        'ALTER TABLE `non-default_db_table` RENAME TO `tests_testmodel_renamed_field`;',
}


sql_mutation = {
    'SQLMutationSequence': """[
...    SQLMutation('first-two-fields', [
...        'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field1` integer NULL;',
...        'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field2` integer NULL;'
...    ], update_first_two),
...    SQLMutation('third-field', [
...        'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field3` integer NULL;',
...    ], update_third)]
""",
    'SQLMutationOutput': 
        '\n'.join([
            'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field1` integer NULL;',
            'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field2` integer NULL;',
            'ALTER TABLE `tests_testmodel` ADD COLUMN `added_field3` integer NULL;',
        ]),
}

generics = {
    'DeleteColumnModel': "ALTER TABLE `tests_testmodel` DROP COLUMN `char_field` CASCADE;"    
}

inheritance = {
    'AddToChildModel': 
        '\n'.join([
            'ALTER TABLE `tests_childmodel` ADD COLUMN `added_field` integer ;',
            'UPDATE `tests_childmodel` SET `added_field` = 42 WHERE `added_field` IS NULL;',
            'ALTER TABLE `tests_childmodel` MODIFY COLUMN `added_field` integer NOT NULL;',
        ]),
    'DeleteFromChildModel': 
        'ALTER TABLE `tests_childmodel` DROP COLUMN `int_field` CASCADE;',
}
