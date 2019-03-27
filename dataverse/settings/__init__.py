from __future__ import absolute_import

from dataverse.settings.defaults import *  # noqa

try:
    from dataverse.settings.local import *  # noqa
except ImportError as error:
    pass