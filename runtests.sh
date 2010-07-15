#!/bin/bash
cd tests
if [ "`python -c 'import django; print django.get_version()' 2>/dev/null`" == "1.2.1" ]
  then
    cd testapp
    if which coverage &> /dev/null; then
        coverage run manage.py test cms
        retcode=$?
        coverage xml --omit=parts,/usr/,eggs
        mv *.xml ..
    else
        python manage.py test cms
        retcode=$?
    fi
    cd ..
  else
    echo "setting up test environment (this might take a while)..."
    python bootstrap.py >/dev/null 2>&1
    ./bin/buildout >/dev/null 2>&1
    ./bin/coverage run ./testapp/manage.py test cms
    retcode=$?
    ./bin/coverage xml --omit=parts,/usr/,eggs
fi
cd ..
exit $retcode
