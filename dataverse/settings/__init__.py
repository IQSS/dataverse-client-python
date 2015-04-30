from __future__ import absolute_import

from dataverse.settings.defaults import *

try:
    from dataverse.settings.local import *
except ImportError as error:
    pass