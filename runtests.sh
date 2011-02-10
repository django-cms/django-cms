#!/bin/bash

args=("$@")
num_args=${#args[@]}
index=0

quicktest=false
manage=false

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
            echo "        defaultpython-defaultdjango - runs with default django and installed django version (default)"
            echo "        defaultpython-1.2.X, defaultpython-1.3.X, defaultpython-trunk,"
            echo "        py25-1.2.X, py25-1.3.X, py25-trunk,"
            echo "        py26-1.2.X, py26-1.3.X, py26-trunk,"
            echo "        py27-1.2.X, py27-1.3.X, ALL"
            echo ""
            echo " --quicktest - use already built tox env, for running a simple test quickly"
            echo " --failfast - abort at first failing test"
            echo " --manage - run management shell"
            exit 1
            ;;
        
        "--manage")
            manage=true
            ;;  
        *)
            suite="${args[$index]}"
    esac
let "index = $index + 1"
done



if [ ! "$toxenv" ]; then
    toxenv='defaultpython-defaultdjango'
fi


OLD_IFS=IFS
IFS=","
tox_envs=( $toxenv )
tox_len=${#tox_envs[@]}
IFS=OLD_IFS

if [[ $quicktest == true || $manage == true ]]; then
    if [[ $manage == true ]]; then
        if [[ "$tox_len" -gt "1" || "$toxenv" == "ALL" ]]; then
            echo "Cannot use multiple envs with --manage" 
            exit 1
        fi
        if [ ! -d ".tox/$toxenv" ]; then
            echo ".tox/$toxenv does not exist, run without --manage first"
            exit 1
        fi
        .tox/$toxenv/bin/python cms/test/run_shell.py --direct "$@"
        exit 1
    fi
    if [ "$toxenv" == "ALL" ]; then
        echo "Cannot use ALL with --quicktest" 
        exit 1
    fi
    for tenv in ${tox_envs[@]}; do
        if [ ! -d ".tox/$tenv" ]; then
            echo ".tox/$tenv does not exist, run without --quicktest first"
            exit 1
        fi
        read -p "Hit any key to run tests in tox env $tenv"
        echo "Running cms test $suite using $tenv"
        # running tests without invoking tox to save time
        if [ "$failfast" ]; then
            echo "--failfast supplied, not using xmlrunner."
        fi
        .tox/$tenv/bin/python cms/test/run_tests.py --toxenv $tenv --direct $failfast $suite 
        retcode=$?
    done
else
    if [ "$suite" ]; then
        echo "Can only run specific suite with --quicktest"
    fi
    
    if [ ! -f "toxinstall/bin/tox" ]; then
        echo "Installing tox"
        virtualenv toxinstall
        toxinstall/bin/pip install -U tox
    fi
    echo "Running complete cms testsuite."
    toxinstall/bin/tox -e $toxenv
    retcode=$?
fi
exit $retcode