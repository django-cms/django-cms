from debug_toolbar.panels import DebugPanel
from django.db import connection
from django.db.backends import util
from django.template.loader import render_to_string
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.utils import simplejson
import time
import os.path
import inspect

class DatabaseStatTracker(util.CursorDebugWrapper):
    """Replacement for CursorDebugWrapper which stores additional information
    in `connection.queries`."""
    
    def execute(self, sql, params=()):
        start = time.time()
        try:
            return self.cursor.execute(sql, params)
        finally:
            try:
                stack = [s[1:] for s in inspect.stack()[1:]]
            except:
                # Strange issue cropped up sometimes
                stack = []
            stop = time.time()
            # We keep `sql` to maintain backwards compatibility
            self.db.queries.append({
                'sql': self.db.ops.last_executed_query(self.cursor, sql, params),
                'time': (stop - start)*1000,
                'raw_sql': sql,
                'params': params,
                'stack': stack,
            })

util.CursorDebugWrapper = DatabaseStatTracker

class SQLDebugPanel(DebugPanel):
    """
    Panel that displays information about the SQL queries run while processing the request.
    """
    name = 'SQL'

    def process_ajax(self, request):
        action = request.GET.get('op')
        if action == 'explain':
            # make sure its only the first query that we're executing
            # TODO: loop through each sql statement to output explain?
            # TODO: this breaks if ; is inside an enclosure
            sql = request.GET.get('sql', '').split(';')[0]
            if sql.lower().startswith('select'):
                params = request.GET.get('params', '')
                if params: params = simplejson.loads(params)
                cursor = connection.cursor()
                cursor.execute("EXPLAIN %s" % (sql,), params)
                response = cursor.fetchall()
                headers = [h[0].replace('_', ' ') for h in cursor.description]
                context = {
                    'headers': headers,
                    'explain': response,
                    'sql': sql,
                    'params': params,
                }
                cursor.close()
                # Do an explain on indexes
                # TODO: mySQL only at the moment
                if headers[2] == 'table':
                    cursor = connection.cursor()
                    indexes = {}
                    for row in response:
                        table_name = row[2]
                        if table_name and table_name not in indexes and not table_name.startswith('<'):
                            cursor = connection.cursor()
                            cursor.execute("SHOW INDEX FROM `%s`" % (row[2],))
                            indexes[table_name] = {}
                            for index in cursor.fetchall():
                                name, column, unique_flag, cardinality, itype = index[2], index[4], index[1], index[6], index[10]
                                # Being that only my local copy of MySQL 5.1.x (Beta)
                                # shows this as false on uniques, and the release copy of
                                # 5.x shows it as true, we're going to assume true
                                # is correct
                                if unique_flag:
                                    typename = 'UNIQUE %s' % (itype,)
                                else:
                                    typename = itype
                                if name not in indexes[table_name]:
                                    indexes[table_name][name] = ([], typename, cardinality)
                                indexes[table_name][name][0].append(column)
                    context.update({
                        'indexes': indexes,
                    })
                    cursor.close()
                return render_to_response('debug_toolbar/panels/sql_explain.html', context)
            else:
                return HttpResponse('Invalid SQL', mimetype="text/plain")
    
    def process_request(self, request):
        self.queries_offset = len(connection.queries)
    
    def process_response(self, request, response):
        self.queries = connection.queries[self.queries_offset:]
        self.total_time = sum(map(lambda q: q['time'], self.queries))
        return response

    def has_content(self):
        return bool(self.queries)

    def title(self):
        return 'SQL: %.2fms (%d queries)' % (self.total_time, len(self.queries))

    def url(self):
        return ''

    def content(self):
        queries = [(q['time'], q['sql'], q['raw_sql'], q['params'], q['stack']) for q in sorted(self.queries, key=lambda x: x['time'])[::-1]]

        query_groups = {}
        for item in queries:
            time, raw_sql = item[0], item[2]
            group = query_groups.get(raw_sql, (0, 0))
            query_groups[raw_sql] = (group[0]+time, group[1]+1)
        query_groups = sorted([(k, v[0], v[1]) for k, v in query_groups.iteritems()], key=lambda x: x[1])[::-1]
        
        context = {
            'queries': queries,
            'query_groups': query_groups,
        }
        return render_to_string('debug_toolbar/panels/sql.html', context)