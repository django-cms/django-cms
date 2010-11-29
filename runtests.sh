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

args=("$@")
num_args=${#args[@]}
index=0

while [ "$index" -lt "$num_args" ]
do
    if [ "${args[$index]}" = "--failfast" ]; then
        failfast="--failfast"
        
    else
        suite="cms.${args[$index]}"
    fi
    let "index = $index + 1"
done

if [ "$failfast" ]; then
    echo "--failfast supplied, not using xmlrunner."
fi

if [ ! "$suite" ]; then
    suite="cms"
    echo "Running complete cms testsuite."
else
    echo "Running cms test $suite."
fi

./bin/coverage run --rcfile=.coveragerc testapp/manage.py test $suite $failfast
retcode=$?
echo "Post test actions..."
./bin/coverage xml
./bin/coverage html
cd ..
echo "done"
exit $retcode
