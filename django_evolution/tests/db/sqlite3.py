add_field = {
    'AddNonNullNonCallableColumnModel':
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "id", "char_field", "added_field" FROM "tests_testmodel";',
            'UPDATE "TEMP_TABLE" SET "added_field" = 1;',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NOT NULL);',
            'INSERT INTO "tests_testmodel" ("int_field", "id", "char_field", "added_field") SELECT "int_field", "id", "char_field", "added_field" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'AddNonNullCallableColumnModel':
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "id", "char_field", "added_field" FROM "tests_testmodel";',
            'UPDATE "TEMP_TABLE" SET "added_field" = "int_field";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NOT NULL);',
            'INSERT INTO "tests_testmodel" ("int_field", "id", "char_field", "added_field") SELECT "int_field", "id", "char_field", "added_field" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'AddNullColumnWithInitialColumnModel':
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "id", "char_field", "added_field" FROM "tests_testmodel";',
            'UPDATE "TEMP_TABLE" SET "added_field" = 1;',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NULL);',
            'INSERT INTO "tests_testmodel" ("int_field", "id", "char_field", "added_field") SELECT "int_field", "id", "char_field", "added_field" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'AddStringColumnModel':
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" varchar(10) NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "id", "char_field", "added_field" FROM "tests_testmodel";',
            'UPDATE "TEMP_TABLE" SET "added_field" = \'abc\\\'s xyz\';',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" varchar(10) NOT NULL);',
            'INSERT INTO "tests_testmodel" ("int_field", "id", "char_field", "added_field") SELECT "int_field", "id", "char_field", "added_field" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'AddDateColumnModel':
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" datetime NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "id", "char_field", "added_field" FROM "tests_testmodel";',
            'UPDATE "TEMP_TABLE" SET "added_field" = 2007-12-13 16:42:00;',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" datetime NOT NULL);',
            'INSERT INTO "tests_testmodel" ("int_field", "id", "char_field", "added_field") SELECT "int_field", "id", "char_field", "added_field" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'AddDefaultColumnModel':
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "id", "char_field", "added_field" FROM "tests_testmodel";',
            'UPDATE "TEMP_TABLE" SET "added_field" = 42;',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NOT NULL);',
            'INSERT INTO "tests_testmodel" ("int_field", "id", "char_field", "added_field") SELECT "int_field", "id", "char_field", "added_field" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'AddEmptyStringDefaultColumnModel':
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" varchar(20) NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "id", "char_field", "added_field" FROM "tests_testmodel";',
            'UPDATE "TEMP_TABLE" SET "added_field" = \'\';',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" varchar(20) NOT NULL);',
            'INSERT INTO "tests_testmodel" ("int_field", "id", "char_field", "added_field") SELECT "int_field", "id", "char_field", "added_field" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'AddNullColumnModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "id", "char_field", "added_field" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NULL);',
            'INSERT INTO "tests_testmodel" ("int_field", "id", "char_field", "added_field") SELECT "int_field", "id", "char_field", "added_field" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'NonDefaultColumnModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "non-default_column" integer NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "id", "char_field", "non-default_column" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "non-default_column" integer NULL);',
            'INSERT INTO "tests_testmodel" ("int_field", "id", "char_field", "non-default_column") SELECT "int_field", "id", "char_field", "non-default_column" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'AddColumnCustomTableModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("id" integer NOT NULL UNIQUE PRIMARY KEY, "value" integer NOT NULL, "alt_value" varchar(20) NOT NULL, "added_field" integer NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "id", "value", "alt_value", "added_field" FROM "custom_table_name";',
            'DROP TABLE "custom_table_name";',
            'CREATE TABLE "custom_table_name"("id" integer NOT NULL UNIQUE PRIMARY KEY, "value" integer NOT NULL, "alt_value" varchar(20) NOT NULL, "added_field" integer NULL);',
            'INSERT INTO "custom_table_name" ("id", "value", "alt_value", "added_field") SELECT "id", "value", "alt_value", "added_field" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'AddIndexedColumnModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "add_field" integer NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "id", "char_field", "add_field" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "add_field" integer NULL);',
            'INSERT INTO "tests_testmodel" ("int_field", "id", "char_field", "add_field") SELECT "int_field", "id", "char_field", "add_field" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
            'CREATE INDEX "tests_testmodel_add_field" ON "tests_testmodel" ("add_field");',
        ]),
    'AddUniqueColumnModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NULL UNIQUE);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "id", "char_field", "added_field" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NULL UNIQUE);',
            'INSERT INTO "tests_testmodel" ("int_field", "id", "char_field", "added_field") SELECT "int_field", "id", "char_field", "added_field" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'AddUniqueIndexedModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NULL UNIQUE);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "id", "char_field", "added_field" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NULL UNIQUE);',
            'INSERT INTO "tests_testmodel" ("int_field", "id", "char_field", "added_field") SELECT "int_field", "id", "char_field", "added_field" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'AddForeignKeyModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field_id" integer NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "id", "char_field", "added_field_id" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field_id" integer NULL);',
            'INSERT INTO "tests_testmodel" ("int_field", "id", "char_field", "added_field_id") SELECT "int_field", "id", "char_field", "added_field_id" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
            'CREATE INDEX "tests_testmodel_added_field_id" ON "tests_testmodel" ("added_field_id");',
        ]),
    'AddManyToManyDatabaseTableModel': 
        '\n'.join([
            'CREATE TABLE "tests_testmodel_added_field" (',
            '    "id" integer NOT NULL PRIMARY KEY,',
            '    "testmodel_id" integer NOT NULL REFERENCES "tests_testmodel" ("id"),',
            '    "addanchor1_id" integer NOT NULL REFERENCES "tests_addanchor1" ("id"),',
            '    UNIQUE ("testmodel_id", "addanchor1_id")',
            ')',
            ';',
        ]),
     'AddManyToManyNonDefaultDatabaseTableModel': 
        '\n'.join([
            'CREATE TABLE "tests_testmodel_added_field" (',
            '    "id" integer NOT NULL PRIMARY KEY,',
            '    "testmodel_id" integer NOT NULL REFERENCES "tests_testmodel" ("id"),',
            '    "addanchor2_id" integer NOT NULL REFERENCES "custom_add_anchor_table" ("id"),',
            '    UNIQUE ("testmodel_id", "addanchor2_id")',
            ')',
            ';',
        ]),
     'AddManyToManySelf': 
        '\n'.join([
            'CREATE TABLE "tests_testmodel_added_field" (',
            '    "id" integer NOT NULL PRIMARY KEY,',
            '    "from_testmodel_id" integer NOT NULL REFERENCES "tests_testmodel" ("id"),',
            '    "to_testmodel_id" integer NOT NULL REFERENCES "tests_testmodel" ("id"),',
            '    UNIQUE ("from_testmodel_id", "to_testmodel_id")',
            ')',
            ';',
        ]),
}

delete_field = {
    'DefaultNamedColumnModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("non-default_db_column" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "fk_field1_id" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'INSERT INTO "TEMP_TABLE" SELECT "non-default_db_column", "int_field3", "fk_field1_id", "char_field", "my_id" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("non-default_db_column" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "fk_field1_id" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'CREATE INDEX "tests_testmodel_fk_field1_id" ON "tests_testmodel" ("fk_field1_id");',
            'INSERT INTO "tests_testmodel" ("non-default_db_column", "int_field3", "fk_field1_id", "char_field", "my_id") SELECT "non-default_db_column", "int_field3", "fk_field1_id", "char_field", "my_id" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'NonDefaultNamedColumnModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "fk_field1_id" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "int_field3", "fk_field1_id", "char_field", "my_id" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "fk_field1_id" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'CREATE INDEX "tests_testmodel_fk_field1_id" ON "tests_testmodel" ("fk_field1_id");',
            'INSERT INTO "tests_testmodel" ("int_field", "int_field3", "fk_field1_id", "char_field", "my_id") SELECT "int_field", "int_field3", "fk_field1_id", "char_field", "my_id" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'ConstrainedColumnModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "non-default_db_column" integer NOT NULL, "fk_field1_id" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "non-default_db_column", "fk_field1_id", "char_field", "my_id" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "non-default_db_column" integer NOT NULL, "fk_field1_id" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'CREATE INDEX "tests_testmodel_fk_field1_id" ON "tests_testmodel" ("fk_field1_id");',
            'INSERT INTO "tests_testmodel" ("int_field", "non-default_db_column", "fk_field1_id", "char_field", "my_id") SELECT "int_field", "non-default_db_column", "fk_field1_id", "char_field", "my_id" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'DefaultManyToManyModel': 
        'DROP TABLE "tests_testmodel_m2m_field1";',
    'NonDefaultManyToManyModel': 
        'DROP TABLE "non-default_m2m_table";',
    'DeleteForeignKeyModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "non-default_db_column" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "non-default_db_column", "int_field3", "char_field", "my_id" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "non-default_db_column" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'INSERT INTO "tests_testmodel" ("int_field", "non-default_db_column", "int_field3", "char_field", "my_id") SELECT "int_field", "non-default_db_column", "int_field3", "char_field", "my_id" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'DeleteColumnCustomTableModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("id" integer NOT NULL UNIQUE PRIMARY KEY, "alt_value" varchar(20) NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "id", "alt_value" FROM "custom_table_name";',
            'DROP TABLE "custom_table_name";',
            'CREATE TABLE "custom_table_name"("id" integer NOT NULL UNIQUE PRIMARY KEY, "alt_value" varchar(20) NOT NULL);',
            'INSERT INTO "custom_table_name" ("id", "alt_value") SELECT "id", "alt_value" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
}

change_field = {
    "SetNotNullChangeModelWithConstant":
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NOT NULL, "char_field2" varchar(30) NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'UPDATE "TEMP_TABLE" SET "char_field1" = \'abc\\\'s xyz\';',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NOT NULL, "char_field2" varchar(30) NOT NULL);',
            'INSERT INTO "tests_testmodel" ("int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    "SetNotNullChangeModelWithCallable":
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NOT NULL, "char_field2" varchar(30) NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'UPDATE "TEMP_TABLE" SET "char_field1" = "char_field";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NOT NULL, "char_field2" varchar(30) NOT NULL);',
            'INSERT INTO "tests_testmodel" ("int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    "SetNullChangeModel": 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NULL);',
            'INSERT INTO "tests_testmodel" ("int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    "NoOpChangeModel": '',
    "IncreasingMaxLengthChangeModel": 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(45) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(45) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NOT NULL);',
            'INSERT INTO "tests_testmodel" ("int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    "DecreasingMaxLengthChangeModel": 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(1) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(1) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NOT NULL);',
            'INSERT INTO "tests_testmodel" ("int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    "DBColumnChangeModel": 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL, "customised_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL, "customised_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NOT NULL);',
            'CREATE INDEX "tests_testmodel_int_field1" ON "tests_testmodel" ("int_field1");',
            'INSERT INTO "tests_testmodel" ("int_field4", "customised_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "customised_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    "M2MDBTableChangeModel": 'ALTER TABLE "change_field_non-default_m2m_table" RENAME TO "custom_m2m_db_table_name";',
    "AddDBIndexChangeModel": 'CREATE INDEX "tests_testmodel_int_field2" ON "tests_testmodel" ("int_field2");',
    "RemoveDBIndexChangeModel": 'DROP INDEX "tests_testmodel_int_field1";',
    "AddUniqueChangeModel": 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL UNIQUE, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL UNIQUE, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NOT NULL);',
            'INSERT INTO "tests_testmodel" ("int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    "RemoveUniqueChangeModel": 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NOT NULL);',
            'INSERT INTO "tests_testmodel" ("int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    "MultiAttrChangeModel": 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NULL);',
            'INSERT INTO "tests_testmodel" ("int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL, "custom_db_column2" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL, "custom_db_column2" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NULL);',
            'CREATE INDEX "tests_testmodel_int_field1" ON "tests_testmodel" ("int_field1");',
            'INSERT INTO "tests_testmodel" ("int_field4", "custom_db_column2", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "custom_db_column2", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL, "custom_db_column2" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(35) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column2", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL, "custom_db_column2" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(35) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NULL);',
            'INSERT INTO "tests_testmodel" ("int_field4", "custom_db_column2", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "custom_db_column2", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    "MultiAttrSingleFieldChangeModel": 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(35) NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(35) NOT NULL);',
            'INSERT INTO "tests_testmodel" ("int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(35) NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(35) NULL);',
            'INSERT INTO "tests_testmodel" ("int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    "RedundantAttrsChangeModel":
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL, "custom_db_column" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NULL);',
            'INSERT INTO "tests_testmodel" ("int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL, "custom_db_column3" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL, "custom_db_column3" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(20) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NULL);',
            'CREATE INDEX "tests_testmodel_int_field1" ON "tests_testmodel" ("int_field1");',
            'INSERT INTO "tests_testmodel" ("int_field4", "custom_db_column3", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "custom_db_column3", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field4" integer NOT NULL, "custom_db_column3" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(35) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field4", "custom_db_column3", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field4" integer NOT NULL, "custom_db_column3" integer NOT NULL, "int_field1" integer NOT NULL, "int_field2" integer NOT NULL, "int_field3" integer NOT NULL UNIQUE, "alt_pk" integer NOT NULL, "char_field" varchar(35) NOT NULL, "my_id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field1" varchar(25) NULL, "char_field2" varchar(30) NULL);',
            'INSERT INTO "tests_testmodel" ("int_field4", "custom_db_column3", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2") SELECT "int_field4", "custom_db_column3", "int_field1", "int_field2", "int_field3", "alt_pk", "char_field", "my_id", "char_field1", "char_field2" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
}

delete_model = {
    'BasicModel': 
        'DROP TABLE "tests_basicmodel";',
    'BasicWithM2MModel': 
        '\n'.join([
            'DROP TABLE "tests_basicwithm2mmodel_m2m";',
            'DROP TABLE "tests_basicwithm2mmodel";'
        ]),
    'CustomTableModel': 
        'DROP TABLE "custom_table_name";',
    'CustomTableWithM2MModel': 
        '\n'.join([
            'DROP TABLE "another_custom_table_name_m2m";',
            'DROP TABLE "another_custom_table_name";'
        ]),
}

delete_application = {
    'DeleteApplication':
        '\n'.join([
            'DROP TABLE "tests_appdeleteanchor1";',
            'DROP TABLE "tests_testmodel_anchor_m2m";',
            'DROP TABLE "tests_testmodel";',
            'DROP TABLE "app_delete_custom_add_anchor_table";',
            'DROP TABLE "app_delete_custom_table_name";',
        ]),
}

rename_field = {
    'RenameColumnModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("custom_db_col_name" integer NOT NULL, "char_field" varchar(20) NOT NULL, "renamed_field" integer NOT NULL, "custom_db_col_name_indexed" integer NOT NULL, "fk_field_id" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'INSERT INTO "TEMP_TABLE" SELECT "custom_db_col_name", "char_field", "int_field", "custom_db_col_name_indexed", "fk_field_id", "id" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("custom_db_col_name" integer NOT NULL, "char_field" varchar(20) NOT NULL, "renamed_field" integer NOT NULL, "custom_db_col_name_indexed" integer NOT NULL, "fk_field_id" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'CREATE INDEX "tests_testmodel_custom_db_col_name_indexed" ON "tests_testmodel" ("custom_db_col_name_indexed");',
            'CREATE INDEX "tests_testmodel_fk_field_id" ON "tests_testmodel" ("fk_field_id");',
            'INSERT INTO "tests_testmodel" ("custom_db_col_name", "char_field", "renamed_field", "custom_db_col_name_indexed", "fk_field_id", "id") SELECT "custom_db_col_name", "char_field", "renamed_field", "custom_db_col_name_indexed", "fk_field_id", "id" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'RenameColumnWithTableNameModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("custom_db_col_name" integer NOT NULL, "char_field" varchar(20) NOT NULL, "renamed_field" integer NOT NULL, "custom_db_col_name_indexed" integer NOT NULL, "fk_field_id" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'INSERT INTO "TEMP_TABLE" SELECT "custom_db_col_name", "char_field", "int_field", "custom_db_col_name_indexed", "fk_field_id", "id" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("custom_db_col_name" integer NOT NULL, "char_field" varchar(20) NOT NULL, "renamed_field" integer NOT NULL, "custom_db_col_name_indexed" integer NOT NULL, "fk_field_id" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'CREATE INDEX "tests_testmodel_custom_db_col_name_indexed" ON "tests_testmodel" ("custom_db_col_name_indexed");',
            'CREATE INDEX "tests_testmodel_fk_field_id" ON "tests_testmodel" ("fk_field_id");',
            'INSERT INTO "tests_testmodel" ("custom_db_col_name", "char_field", "renamed_field", "custom_db_col_name_indexed", "fk_field_id", "id") SELECT "custom_db_col_name", "char_field", "renamed_field", "custom_db_col_name_indexed", "fk_field_id", "id" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'RenamePrimaryKeyColumnModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("custom_db_col_name" integer NOT NULL, "char_field" varchar(20) NOT NULL, "int_field" integer NOT NULL, "custom_db_col_name_indexed" integer NOT NULL, "fk_field_id" integer NOT NULL, "my_pk_id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'INSERT INTO "TEMP_TABLE" SELECT "custom_db_col_name", "char_field", "int_field", "custom_db_col_name_indexed", "fk_field_id", "id" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("custom_db_col_name" integer NOT NULL, "char_field" varchar(20) NOT NULL, "int_field" integer NOT NULL, "custom_db_col_name_indexed" integer NOT NULL, "fk_field_id" integer NOT NULL, "my_pk_id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'CREATE INDEX "tests_testmodel_custom_db_col_name_indexed" ON "tests_testmodel" ("custom_db_col_name_indexed");',
            'CREATE INDEX "tests_testmodel_fk_field_id" ON "tests_testmodel" ("fk_field_id");',
            'INSERT INTO "tests_testmodel" ("custom_db_col_name", "char_field", "int_field", "custom_db_col_name_indexed", "fk_field_id", "my_pk_id") SELECT "custom_db_col_name", "char_field", "int_field", "custom_db_col_name_indexed", "fk_field_id", "my_pk_id" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),        
    'RenameForeignKeyColumnModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "char_field" varchar(20) NOT NULL, "custom_db_col_name" integer NOT NULL, "custom_db_col_name_indexed" integer NOT NULL, "renamed_field_id" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "char_field", "custom_db_col_name", "custom_db_col_name_indexed", "fk_field_id", "id" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "char_field" varchar(20) NOT NULL, "custom_db_col_name" integer NOT NULL, "custom_db_col_name_indexed" integer NOT NULL, "renamed_field_id" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'CREATE INDEX "tests_testmodel_custom_db_col_name_indexed" ON "tests_testmodel" ("custom_db_col_name_indexed");',
            'CREATE INDEX "tests_testmodel_renamed_field_id" ON "tests_testmodel" ("renamed_field_id");',
            'INSERT INTO "tests_testmodel" ("int_field", "char_field", "custom_db_col_name", "custom_db_col_name_indexed", "renamed_field_id", "id") SELECT "int_field", "char_field", "custom_db_col_name", "custom_db_col_name_indexed", "renamed_field_id", "id" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'RenameNonDefaultColumnNameModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "char_field" varchar(20) NOT NULL, "renamed_field" integer NOT NULL, "custom_db_col_name_indexed" integer NOT NULL, "fk_field_id" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "char_field", "custom_db_col_name", "custom_db_col_name_indexed", "fk_field_id", "id" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "char_field" varchar(20) NOT NULL, "renamed_field" integer NOT NULL, "custom_db_col_name_indexed" integer NOT NULL, "fk_field_id" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'CREATE INDEX "tests_testmodel_custom_db_col_name_indexed" ON "tests_testmodel" ("custom_db_col_name_indexed");',
            'CREATE INDEX "tests_testmodel_fk_field_id" ON "tests_testmodel" ("fk_field_id");',
            'INSERT INTO "tests_testmodel" ("int_field", "char_field", "renamed_field", "custom_db_col_name_indexed", "fk_field_id", "id") SELECT "int_field", "char_field", "renamed_field", "custom_db_col_name_indexed", "fk_field_id", "id" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'RenameNonDefaultColumnNameToNonDefaultNameModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "char_field" varchar(20) NOT NULL, "non-default_column_name" integer NOT NULL, "custom_db_col_name_indexed" integer NOT NULL, "fk_field_id" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "char_field", "custom_db_col_name", "custom_db_col_name_indexed", "fk_field_id", "id" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "char_field" varchar(20) NOT NULL, "non-default_column_name" integer NOT NULL, "custom_db_col_name_indexed" integer NOT NULL, "fk_field_id" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'CREATE INDEX "tests_testmodel_custom_db_col_name_indexed" ON "tests_testmodel" ("custom_db_col_name_indexed");',
            'CREATE INDEX "tests_testmodel_fk_field_id" ON "tests_testmodel" ("fk_field_id");',
            'INSERT INTO "tests_testmodel" ("int_field", "char_field", "non-default_column_name", "custom_db_col_name_indexed", "fk_field_id", "id") SELECT "int_field", "char_field", "non-default_column_name", "custom_db_col_name_indexed", "fk_field_id", "id" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'RenameNonDefaultColumnNameToNonDefaultNameAndTableModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "char_field" varchar(20) NOT NULL, "non-default_column_name2" integer NOT NULL, "custom_db_col_name_indexed" integer NOT NULL, "fk_field_id" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "char_field", "custom_db_col_name", "custom_db_col_name_indexed", "fk_field_id", "id" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "char_field" varchar(20) NOT NULL, "non-default_column_name2" integer NOT NULL, "custom_db_col_name_indexed" integer NOT NULL, "fk_field_id" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY);',
            'CREATE INDEX "tests_testmodel_custom_db_col_name_indexed" ON "tests_testmodel" ("custom_db_col_name_indexed");',
            'CREATE INDEX "tests_testmodel_fk_field_id" ON "tests_testmodel" ("fk_field_id");',
            'INSERT INTO "tests_testmodel" ("int_field", "char_field", "non-default_column_name2", "custom_db_col_name_indexed", "fk_field_id", "id") SELECT "int_field", "char_field", "non-default_column_name2", "custom_db_col_name_indexed", "fk_field_id", "id" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'RenameColumnCustomTableModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("id" integer NOT NULL UNIQUE PRIMARY KEY, "renamed_field" integer NOT NULL, "alt_value" varchar(20) NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "id", "value", "alt_value" FROM "custom_rename_table_name";',
            'DROP TABLE "custom_rename_table_name";',
            'CREATE TABLE "custom_rename_table_name"("id" integer NOT NULL UNIQUE PRIMARY KEY, "renamed_field" integer NOT NULL, "alt_value" varchar(20) NOT NULL);',
            'INSERT INTO "custom_rename_table_name" ("id", "renamed_field", "alt_value") SELECT "id", "renamed_field", "alt_value" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'RenameManyToManyTableModel': 
        'ALTER TABLE "tests_testmodel_m2m_field" RENAME TO "tests_testmodel_renamed_field";',
    'RenameManyToManyTableWithColumnNameModel': 
        'ALTER TABLE "tests_testmodel_m2m_field" RENAME TO "tests_testmodel_renamed_field";',
    'RenameNonDefaultManyToManyTableModel': 
        'ALTER TABLE "non-default_db_table" RENAME TO "tests_testmodel_renamed_field";',
}

sql_mutation = {
    'SQLMutationSequence': """[
...    SQLMutation('first-two-fields', [
...        'ALTER TABLE "tests_testmodel" ADD COLUMN "added_field1" integer NULL;',
...        'ALTER TABLE "tests_testmodel" ADD COLUMN "added_field2" integer NULL;'
...    ], update_first_two),
...    SQLMutation('third-field', [
...        'ALTER TABLE "tests_testmodel" ADD COLUMN "added_field3" integer NULL;',
...    ], update_third)]
""",
    'SQLMutationOutput': 
        '\n'.join([
            'ALTER TABLE "tests_testmodel" ADD COLUMN "added_field1" integer NULL;',
            'ALTER TABLE "tests_testmodel" ADD COLUMN "added_field2" integer NULL;',
            'ALTER TABLE "tests_testmodel" ADD COLUMN "added_field3" integer NULL;',
        ]),
}

generics = {
    'DeleteColumnModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "content_type_id" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "object_id" integer unsigned NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "content_type_id", "id", "object_id" FROM "tests_testmodel";',
            'DROP TABLE "tests_testmodel";',
            'CREATE TABLE "tests_testmodel"("int_field" integer NOT NULL, "content_type_id" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "object_id" integer unsigned NOT NULL);',
            'CREATE INDEX "tests_testmodel_content_type_id" ON "tests_testmodel" ("content_type_id");',
            'CREATE INDEX "tests_testmodel_object_id" ON "tests_testmodel" ("object_id");',
            'INSERT INTO "tests_testmodel" ("int_field", "content_type_id", "id", "object_id") SELECT "int_field", "content_type_id", "id", "object_id" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ])
}

inheritance = {
    'AddToChildModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "int_field", "id", "char_field", "added_field" FROM "tests_childmodel";',
            'UPDATE "TEMP_TABLE" SET "added_field" = 42;',
            'DROP TABLE "tests_childmodel";',
            'CREATE TABLE "tests_childmodel"("int_field" integer NOT NULL, "id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL, "added_field" integer NOT NULL);',
            'INSERT INTO "tests_childmodel" ("int_field", "id", "char_field", "added_field") SELECT "int_field", "id", "char_field", "added_field" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";',
        ]),
    'DeleteFromChildModel': 
        '\n'.join([
            'CREATE TEMPORARY TABLE "TEMP_TABLE"("id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL);',
            'INSERT INTO "TEMP_TABLE" SELECT "id", "char_field" FROM "tests_childmodel";',
            'DROP TABLE "tests_childmodel";',
            'CREATE TABLE "tests_childmodel"("id" integer NOT NULL UNIQUE PRIMARY KEY, "char_field" varchar(20) NOT NULL);',
            'INSERT INTO "tests_childmodel" ("id", "char_field") SELECT "id", "char_field" FROM "TEMP_TABLE";',
            'DROP TABLE "TEMP_TABLE";'
        ])
}