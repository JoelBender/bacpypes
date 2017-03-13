#!/bin/bash

# remove everything in the current dist/ directory
[ -d dist ] && rm -Rfv dist

# start with a clean build directory
rm -Rfv build/

# Python 2.5 doesn't support wheels
# python2.5 setup.py bdist_egg
# rm -Rfv build/

for ver in 2.7 3.5; do
    python$ver setup.py bdist_egg
    python$ver setup.py bdist_wheel
    rm -Rfv build/
done

read -p "Upload to PyPI? [y/n/x] " yesno || exit 1

if [ "$yesno" = "y" ] ;
then
    twine upload dist/*
elif [ "$yesno" = "n" ] ;
then
    echo "Skipped..."
else
    echo "exit..."
    exit 1
fi

