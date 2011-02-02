#!/bin/bash

args=("$@")
num_args=${#args[@]}
index=0

quicktest=false
disable_coverage=true

while [ "$index" -lt "$num_args" ]
do
case "${args[$index]}" in
        "--failfast")
            failfast="--failfast"
            ;;

        "--with-coverage")
            disable_coverage=false
            ;;
         
        "--toxenv")
            let "index = $index + 1"
            toxenv="${args[$index]}"
            ;;
            
        "--quicktest")
            quicktest=true
            ;;
            
        "--help")
            echo ""
            echo "usage:"
            echo " runtests.sh"
            echo " or runtests.sh [testcase]"
            echo " or runtests.sh [flags] [testcase]"
            echo ""
            echo "flags:"
            echo " --toxenv [tox-env]"
            echo "    eg. runtests.sh --toxenv py26-1.2.X,py26-trunk"
            echo " --quicktest - use already built tox env, for running a simple test quickly"
            echo " --failfast - abort at first failing test"
            echo " --with-coverage - enables coverage"
            exit 1
            ;;

        *)
            suite="${args[$index]}"
    esac
let "index = $index + 1"
done

echo "using python at: $python"

if [ ! "$toxenv" ]; then
    toxenv='ALL'
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

if [ ! "$suite" ]; then
    suite="cms"
    echo "Running complete cms testsuite."
else
    echo "Running cms test $suite."
fi

if [ $quicktest == true ]; then
    .tox/$toxenv/bin/python cms/test/run_tests.py --direct $failfast $suite
    retcode=$?
else
    tox -e $toxenv
    retcode=$?
fi
    
echo "done"
exit $retcode