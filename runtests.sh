#!/bin/bash
cd tests
echo "setting up test environment (this might take a while)..."
python bootstrap.py >/dev/null 2>&1
./bin/buildout >/dev/null 2>&1
if [ $1 ]; then
    suite="cms.$1"
else
    suite='cms'
fi
./bin/coverage run ./testapp/manage.py test $suite
retcode=$?
./bin/coverage xml --omit=parts,/usr/,eggs
./bin/coverage html --omit=parts,/usr/,eggs
cd ..
exit $retcode