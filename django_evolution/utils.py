from django_evolution.db import evolver

def write_sql(sql):
    "Output a list of SQL statements, unrolling parameters as required"
    for statement in sql:
        if isinstance(statement, tuple):
            print unicode(statement[0] % tuple(evolver.quote_sql_param(s) for s in statement[1]))
        else:
            print unicode(statement)

def execute_sql(cursor, sql):
    """
    Execute a list of SQL statements on the provided cursor, unrolling 
    parameters as required
    """
    for statement in sql:
        if isinstance(statement, tuple):
            if not statement[0].startswith('--'):
                cursor.execute(*statement)
        else:
            if not statement.startswith('--'):
                cursor.execute(statement)  
