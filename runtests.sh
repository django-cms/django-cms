#!/bin/bash
cd tests
echo "setting up test environment (this might take a while)..."
python bootstrap.py
if [ $? != 0 ]; then
    echo "bootstrap.py failed"
    exit 1
fi
./bin/buildout
if [ $? != 0 ]; then
    echo "bin/buildout failed"
    exit 1
fi
echo "running tests"
if [ $1 ]; then
    suite="cms.$1"
else
    suite='cms'
fi
./bin/coverage run --rcfile=.coveragerc testapp/manage.py test $suite
retcode=$?
echo "post test actions..."
./bin/coverage xml
./bin/coverage html
cd ..
echo "done"
exit $retcode
