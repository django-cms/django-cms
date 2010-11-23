#!/bin/bash
cd tests
echo "setting up test environment (this might take a while)..."

echo "running tests"
if [ $1 ]; then
	if [ "$1" = '--failfast' ]; then
		failfast='--failfast'
		suite='cms'
	else
		suite="cms.$1"
	fi
else
    suite='cms'
fi
./bin/coverage run --rcfile=.coveragerc testapp/manage.py test $suite $failfast
retcode=$?
echo "post test actions..."
./bin/coverage xml
./bin/coverage html
cd ..
echo "done"
exit $retcode
