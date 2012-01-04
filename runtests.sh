#!/bin/bash
find . -name '*.pyc' -delete

cd tests

sigfile=.buildoutsig

args=("$@")
num_args=${#args[@]}
index=0

reuse_env=true
disable_coverage=true
django=12

python="python" # to ensure this script works if no python option is specified
while [ "$index" -lt "$num_args" ]
do
    case "${args[$index]}" in
        "-f"|"--failfast")
            failfast="--failfast"
            ;;

        "-r"|"--rebuild-env")
            reuse_env=false
            ;;

        "-c"|"--with-coverage")
            disable_coverage=false
            ;;
         
        "-d"|"--django")
            let "index = $index + 1"
            django="${args[$index]}"
            ;;
        
        "-p"|"--python")
            let "index = $index + 1"
            python="${args[$index]}"
            ;;

        "-h"|"--help")
            echo ""
            echo "usage:"
            echo "    runtests.sh"
            echo "    or runtests.sh [testcase]"
            echo "    or runtests.sh [flags] [testcase]"
            echo ""
            echo "flags:"
            echo "    -f, --failfast - abort at first failing test"
            echo "    -c, --with-coverage - enables coverage"
            echo "    -r, --rebuild-env - run buildout before the tests"
            echo "    -d, --django <version> - run tests against a django version, options: 12, 13 or trunk"
            echo "    -p, --python /path/to/python - python version to use to run the tests"
            echo "    -h, --help - display this help"
            exit 1
            ;;

        *)
            suite="cms.${args[$index]}"
    esac
    let "index = $index + 1"
done

echo "using python at: $python"

sig="py:$python;dj:$django$"

oldsig="nosig"

if [ -f $sigfile ]; then
    oldsig=`cat $sigfile`
fi

if [ "$oldsig" != "$sig" ]; then
    reuse_env=false
fi

echo $sig > $sigfile

if [ $reuse_env == false ]; then
    echo "setting up test environment (this might take a while)..."
    $python bootstrap.py
    if [ $? != 0 ]; then
        echo "bootstrap.py failed"
        exit 1
    fi
    ./bin/buildout -c "django-$django.cfg"
    if [ $? != 0 ]; then
        echo "bin/buildout failed"
        exit 1
    fi
else
    echo "reusing current buildout environment"
fi

if [ "$failfast" ]; then
    echo "--failfast supplied, not using xmlrunner."
fi

if [ ! "$suite" ]; then
    suite="cms"
    echo "Running complete cms testsuite."
else
    echo "Running cms test $suite."
fi

if [ $disable_coverage == false ]; then
    ./bin/coverage run --rcfile=.coveragerc bin/django test $suite $failfast
    retcode=$?

    echo "Post test actions..."
    ./bin/coverage xml
    ./bin/coverage html
else
    ./bin/django test $suite $failfast
    retcode=$?
fi
cd ..
echo "done"
exit $retcode
