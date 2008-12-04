import unittest

from signature import tests as signature_tests
from add_field import tests as add_field_tests
from delete_field import tests as delete_field_tests
from delete_model import tests as delete_model_tests
from delete_app import tests as delete_app_tests
from rename_field import tests as rename_field_tests
from change_field import tests as change_field_tests
from sql_mutation import tests as sql_mutation_tests
from ordering import tests as ordering_tests
from generics import tests as generics_tests
from inheritance import tests as inheritance_tests
# Define doctests
__test__ = {
    'signature': signature_tests,
    'add_field': add_field_tests,
    'delete_field': delete_field_tests,
    'delete_model': delete_model_tests,
    'delete_app': delete_app_tests,
    'rename_field': rename_field_tests,
    'change_field': change_field_tests,
    'sql_mutation': sql_mutation_tests,
    'ordering': ordering_tests,
    'generics': generics_tests,
    'inheritance': inheritance_tests
}
