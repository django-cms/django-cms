import os
import sys
import copy

from django.core.management.color import color_style
from django.db import transaction, connection
from django.db.models import loading

from django_evolution import EvolutionException, CannotSimulate, SimulationFailure
from django_evolution.models import Evolution
from django_evolution.diff import Diff
from django_evolution.mutations import SQLMutation

def get_evolution_sequence(app):
    "Obtain the full evolution sequence for an application"
    try:
        app_name = '.'.join(app.__name__.split('.')[:-1])
        evolution_module = __import__(app_name + '.evolutions',{},{},[''])
        return evolution_module.SEQUENCE
    except:
        return []
    
def get_unapplied_evolutions(app):
    "Obtain the list of unapplied evolutions for an application"
    sequence = get_evolution_sequence(app)
    app_label = app.__name__.split('.')[-2]
    applied = [evo.label for evo in Evolution.objects.filter(app_label=app_label)]
    return [seq for seq in sequence if seq not in applied]
    
def get_mutations(app, evolution_labels):
    """
    Obtain the list of mutations described by the named evolutions.
    """
    # For each item in the evolution sequence. Check each item to see if it is
    # a python file or an sql file.
    try:
        app_name = '.'.join(app.__name__.split('.')[:-1])
        evolution_module = __import__(app_name + '.evolutions',{},{},[''])
    except ImportError:
        return []

    mutations = []
    for label in evolution_labels:
        directory_name = os.path.dirname(evolution_module.__file__)
        sql_file_name = os.path.join(directory_name, label+'.sql')
        if os.path.exists(sql_file_name):
            sql = []
            sql_file = open(sql_file_name)
            for line in sql_file:
                sql.append(line)
            mutations.append(SQLMutation(label, sql))
        else:
            try:
                module_name = [evolution_module.__name__,label]
                module = __import__('.'.join(module_name),{},{},[module_name]);
                mutations.extend(module.MUTATIONS)
            except ImportError, e:
                raise EvolutionException('Error: Failed to find an SQL or Python evolution named %s' % label)
            
    return mutations
