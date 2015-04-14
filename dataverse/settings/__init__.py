from .defaults import *

try:
    from .local import *
except ImportError as error:
    pass