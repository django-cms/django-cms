# Establish the common EvolutionOperations instance, called evolver.

from django.conf import settings

module_name = ['django_evolution.db',settings.DATABASE_ENGINE]
module = __import__('.'.join(module_name),{},{},[''])

evolver = module.EvolutionOperations()

