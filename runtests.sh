#!/bin/bash
cd tests

args=("$@")
num_args=${#args[@]}
index=0

reuse_env=true
disable_coverage=true
django_trunk=false
python="python" # to ensure this script works if no python option is specified
while [ "$index" -lt "$num_args" ]
do
    case "${args[$index]}" in
        "--failfast")
            failfast="--failfast"
            ;;

        "--rebuild-env")
            reuse_env=false
            ;;

        "--with-coverage")
            disable_coverage=false
            ;;
         
        "--django-trunk")
            django_trunk=true
            ;;
        
        "--python")
            let "index = $index + 1"
            python="${args[$index]}"
            ;;

        "--help")
            echo ""
            echo "usage:"
            echo "    runtests.sh"
            echo "    or runtests.sh [testcase]"
            echo "    or runtests.sh [flags] [testcase]"
            echo ""
            echo "flags:"
            echo "    --failfast - abort at first failing test"
            echo "    --with-coverage - enables coverage"
            echo "    --rebuild-env - run buildout before the tests"
            echo "    --django-trunk - run tests against django trunk"
            echo "    --python /path/to/python - python version to use to run the tests"
            exit 1
            ;;

        *)
            suite="cms.${args[$index]}"
    esac
    let "index = $index + 1"
done

echo "using python at: $python"

if [ $reuse_env == false ]; then
    echo "setting up test environment (this might take a while)..."
    $python bootstrap.py
    if [ $? != 0 ]; then
        echo "bootstrap.py failed"
        exit 1
    fi
    if [ $django_trunk == true ]; then
        ./bin/buildout -c django-svn.cfg
    else
        ./bin/buildout
    fi
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
    ./bin/coverage run --rcfile=.coveragerc testapp/manage.py test $suite $failfast
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
