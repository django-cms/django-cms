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
            echo "    possible envs:"
            echo "        py25-1.2.X, py25-1.3.X, py25-trunk"
            echo "        py26-1.2.X, py26-1.3.X, py26-trunk"
            echo "        py27-1.2.X, py27-1.3.X, ALL"
            echo ""
            echo " --quicktest - use already built tox env, for running a simple test quickly"
            echo " --failfast - abort at first failing test"
            echo " --with-coverage - enables coverage"
            exit 1
            ;;
            
        "--rebuild-env")
            # just to make ci run instantly
            ;;
            
        "--with-coverage")
            # just to make ci run instantly
            ;;
            
        *)
            suite="${args[$index]}"
    esac
let "index = $index + 1"
done



if [ ! "$toxenv" ]; then
    toxenv='py26-1.2.X'
fi

if [ "$failfast" ]; then
    echo "--failfast supplied, not using xmlrunner."
fi

if [ ! "$suite" ]; then
    echo "Running complete cms testsuite."
else
    if [ $quicktest == false ]; then
        echo "Can only run specific suite with --quicktest"
        exit 1
    fi
    echo "Running cms test $suite."
fi

if [ ! -f "toxinstall/bin/tox" ]; then
    echo "Installing tox"
    virtualenv toxinstall
    toxinstall/bin/pip install -U tox
fi

if [ $quicktest == true ]; then
    if [ "$toxenv" == "ALL" ]; then
        echo "Cannot use ALL with --quicktest" 
        exit 1
    fi
    IFS=","
    tenvs=( $toxenv )
    for tenv in ${tenvs[@]}; do
        if [ ! -d ".tox/$tenv" ]; then
            echo ".tox/$tenv does not exist, run without --quicktest first"
            exit 1
        fi
        read -p "Hit any key to run tests in tox env $tenv"
        # running tests without invoking tox to save time
        .tox/$tenv/bin/python cms/test/run_tests.py --direct $failfast $suite 
        retcode=$?
    done
else
    toxinstall/bin/tox -e $toxenv
    retcode=$?
fi
exit $retcode