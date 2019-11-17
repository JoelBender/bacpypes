#!/bin/bash

#
#   BACpypes Test Script
#
#   This is an example script for running specific tests
#   and capturing the debugging output where it can be
#   searched for exceptions, errors, failed tests, etc.
#

version=3
options=""
keep=0

while getopts kv:o: OPTION
do
    case $OPTION in
        k)
            # keep the test results, even if it passes
            keep=1
            ;;
        v)
            # which python version
            version=$OPTARG
            ;;
        o)
            options=$OPTARG
            ;;
    esac
done
shift $((OPTIND-1))

# this is where debugging output should go, the name of the
# file matches the name of the script
bugfile=$(basename $0)
bugfile=${bugfile/.sh/.txt}

# debugging file can rotate, set the file size large to keep
# it from rotating a lot
export BACPYPES_DEBUG_FILE=$bugfile
export BACPYPES_MAX_BYTES=10485760

# add the modules or classes that need debugging and redirect
# the output to the file
export BACPYPES_DEBUG=" \
    tests.test_service.helpers.ApplicationNetwork \
    tests.test_service.helpers.SnifferStateMachine \
    tests.state_machine.match_pdu \
    "

# debugging output will open the file 'append' which is
# not very helpful in most cases, remove the existing debugging file
rm -vf $bugfile

# run the tests for a specific file, the additional options
# are passed to pytest
python$version setup.py test --addopts "tests/test_service/test_cov.py $options"

# if all the tests pass, remove the debugging output, otherwise
# display for your enjoyment
if [ $? -eq 0 ]
then
    if [ $keep -eq 0 ]
    then
        rm -vf $bugfile
    fi
else
    less $bugfile
fi
