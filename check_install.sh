#!/bin/bash

for version in 2.7 3.4 3.5 3.6 3.7 3.8;
do
if [ -a "`which python$version`" ]; then
python$version << EOF

import sys
python_version = "%d.%d.%d" % sys.version_info[:3]

try:
    import bacpypes
    print("%s: %s @ %s" %(
        python_version,
        bacpypes.__version__, bacpypes.__file__,
        ))
except ImportError:
    print("%s: not installed" % (
        python_version,
        ))
EOF
fi
done
