from optparse import make_option
import sys
import copy
try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError
from django.db.models import get_apps, get_app, signals
from django.db import connection, transaction

from django_evolution import CannotSimulate, SimulationFailure, EvolutionException
from django_evolution.diff import Diff
from django_evolution.evolve import get_unapplied_evolutions, get_mutations
from django_evolution.models import Version, Evolution
from django_evolution.mutations import DeleteApplication
from django_evolution.signature import create_project_sig
from django_evolution.utils import write_sql, execute_sql

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
        make_option('--hint', action='store_true', dest='hint', default=False,
            help='Generate an evolution script that would update the app.'),
        make_option('--purge', action='store_true', dest='purge', default=False,
            help='Generate evolutions to delete stale applications.'),
        make_option('--sql', action='store_true', dest='compile_sql', default=False,
            help='Compile a Django evolution script into SQL.'),
        make_option('-x','--execute', action='store_true', dest='execute', default=False,
            help='Apply the evolution to the database.'),
    )
    if '--verbosity' not in [opt.get_opt_string() for opt in BaseCommand.option_list]:
        option_list += make_option('-v','--verbosity', action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),

    help = 'Evolve the models in a Django project.'
    args = '<appname appname ...>'

    requires_model_validation = False

    def handle(self, *app_labels, **options):
        verbosity = int(options['verbosity'])
        interactive = options['interactive']
        execute = options['execute']
        compile_sql = options['compile_sql']
        hint = options['hint']
        purge = options['purge']

        # Use the list of all apps, unless app labels are specified.
        if app_labels:
            if execute:
                raise CommandError('Cannot specify an application name when executing evolutions.')
            try:
                app_list = [get_app(app_label) for app_label in app_labels]
            except (ImproperlyConfigured, ImportError), e:
                raise CommandError("%s. Are you sure your INSTALLED_APPS setting is correct?" % e)
        else:
            app_list = get_apps()

        # Iterate over all applications running the mutations
        evolution_required = False
        simulated = True
        sql = []
        new_evolutions = []

        current_proj_sig = create_project_sig()
        current_signature = pickle.dumps(current_proj_sig)

        try:
            latest_version = Version.objects.latest('when')
            database_sig = pickle.loads(str(latest_version.signature))
            diff = Diff(database_sig, current_proj_sig)
        except Evolution.DoesNotExist:
            print self.style.ERROR("Can't evolve yet. Need to set an evolution baseline.")
            sys.exit(1)

        try:
            for app in app_list:
                app_label = app.__name__.split('.')[-2]
                if hint:
                    evolutions = []
                    hinted_evolution = diff.evolution()
                    mutations = hinted_evolution.get(app_label,[])
                else:
                    evolutions = get_unapplied_evolutions(app)
                    mutations = get_mutations(app, evolutions)

                if mutations:
                    app_sql = ['-- Evolve application %s' % app_label]
                    evolution_required = True
                    for mutation in mutations:
                        # Only compile SQL if we want to show it
                        if compile_sql or execute:
                            app_sql.extend(mutation.mutate(app_label, database_sig))

                        # Now run the simulation, which will modify the signatures
                        try:
                            mutation.simulate(app_label, database_sig)
                        except CannotSimulate:
                            simulated = False
                    new_evolutions.extend(Evolution(app_label=app_label, label=label)
                                            for label in evolutions)

                    if not execute:
                        if compile_sql:
                            write_sql(app_sql)
                        else:
                            print '#----- Evolution for %s' % app_label
                            print 'from django_evolution.mutations import *'
                            print 'from django.db import models'
                            print
                            print 'MUTATIONS = ['
                            print '   ',
                            print ',\n    '.join(unicode(m) for m in mutations)
                            print ']'
                            print '#----------------------'

                    sql.extend(app_sql)
                else:
                    if verbosity > 1:
                        print 'Application %s is up to date' % app_label

            # Process the purged applications if requested to do so.
            if purge:
                if diff.deleted:
                    evolution_required = True
                    delete_app = DeleteApplication()
                    purge_sql = []
                    for app_label in diff.deleted:
                        if compile_sql or execute:
                            purge_sql.append('-- Purge application %s' % app_label)
                            purge_sql.extend(delete_app.mutate(app_label, database_sig))
                        delete_app.simulate(app_label, database_sig)

                    if not execute:
                        if compile_sql:
                            write_sql(purge_sql)
                        else:
                            print 'The following application(s) can be purged:'
                            for app_label in diff.deleted:
                                print '    ', app_label
                            print
                    sql.extend(purge_sql)
                else:
                    if verbosity > 1:
                        print 'No applications need to be purged.'

        except EvolutionException, e:
            print self.style.ERROR(e)
            sys.exit(1)

        if simulated:
            diff = Diff(database_sig, current_proj_sig)
            if not diff.is_empty(not purge):
                if hint:
                    print self.style.ERROR('Your models contain changes that Django Evolution cannot resolve automatically.')
                    print 'This is probably due to a currently unimplemented mutation type.'
                    print 'You will need to manually construct a mutation to resolve the remaining changes.'
                else:
                    print self.style.ERROR('The stored evolutions do not completely resolve all model changes.')
                    print 'Run `./manage.py evolve --hint` to see a suggestion for the changes required.'
                print
                print 'The following are the changes that could not be resolved:'
                print diff
                sys.exit(1)
        else:
            print self.style.NOTICE('Evolution could not be simulated, possibly due to raw SQL mutations')

        if evolution_required:
            if execute:
                # Now that we've worked out the mutations required,
                # and we know they simulate OK, run the evolutions
                if interactive:
                    confirm = raw_input("""
You have requested a database evolution. This will alter tables
and data currently in the %r database, and may result in
IRREVERSABLE DATA LOSS. Evolutions should be *thoroughly* reviewed
prior to execution.

Are you sure you want to execute the evolutions?

Type 'yes' to continue, or 'no' to cancel: """ % settings.DATABASE_NAME)
                else:
                    confirm = 'yes'

                if confirm.lower() == 'yes':
                    # Begin Transaction
                    transaction.enter_transaction_management()
                    transaction.managed(True)
                    cursor = connection.cursor()
                    try:
                        # Perform the SQL
                        execute_sql(cursor, sql)

                        # Now update the evolution table
                        version = Version(signature=current_signature)
                        version.save()
                        for evolution in new_evolutions:
                            evolution.version = version
                            evolution.save()

                        transaction.commit()
                    except Exception, ex:
                        transaction.rollback()
                        print self.style.ERROR('Error applying evolution: %s' % str(ex))
                        sys.exit(1)
                    transaction.leave_transaction_management()

                    if verbosity > 0:
                        print 'Evolution successful.'
                else:
                    print self.style.ERROR('Evolution cancelled.')
            elif not compile_sql:
                if verbosity > 0:
                    if simulated:
                        print "Trial evolution successful."
                        print "Run './manage.py evolve %s--execute' to apply evolution." % (hint and '--hint ' or '')
        else:
            if verbosity > 0:
                print 'No evolution required.'
