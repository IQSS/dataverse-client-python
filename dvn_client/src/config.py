DEFAULT_USERNAME = "FIXME"
DEFAULT_PASSWORD = "FIXME"
DEFAULT_HOST = "dvn-4.hmdc.harvard.edu"
DEFAULT_CERT = "../resources/dvn-4.hmdc.harvard.edu"

try:
    from config_local import *
except ImportError:
    pass
