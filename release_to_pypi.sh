#!/bin/bash

for ver in 2.7 3.4; do
    sudo python$ver setup.py bdist_egg
    sudo python$ver setup.py bdist_wheel
done
twine upload dist/*

