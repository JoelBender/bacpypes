#!/bin/bash

python setup.py sdist

for ver in 2.7 3.4; do
    python$ver setup.py bdist_egg
    python$ver setup.py bdist_wheel
done
twine upload dist/*

