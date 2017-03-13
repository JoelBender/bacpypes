#!/usr/bin/python

"""BACnet Python Package"""

#
#   Platform Check
#

import sys as _sys
import warnings as _warnings

_supported_platforms = ('linux2', 'win32', 'darwin')

if _sys.platform not in _supported_platforms:
    _warnings.warn("unsupported platform", RuntimeWarning)

#
#   Project Metadata
#

__version__ = '0.15.0'
__author__ = 'Joel Bender'
__email__ = 'joel@carrickbender.com'

#
#   Communications Core Modules
#

from . import comm
from . import task
from . import singleton
from . import capability
from . import iocb

#
#   Link Layer Modules
#

from . import pdu
from . import vlan

#
#   Network Layer Modules
#

from . import npdu
from . import netservice

#
#   Virtual Link Layer Modules
#

from . import bvll
from . import bvllservice
from . import bsll
from . import bsllservice

#
#   Application Layer Modules
#

from . import primitivedata
from . import constructeddata
from . import basetypes

from . import object

from . import apdu

from . import app
from . import appservice
from . import service

#
#   Analysis
#

from . import analysis
