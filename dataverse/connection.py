from lxml import etree
import requests

from dataverse import Dataverse
from exceptions import DataverseError, UnauthorizedError
from utils import get_elements, is_not_root_dataverse


class Connection(object):

    def __init__(self, host, token=None, username=None, password=None):
        # Connection Properties
        self.token = token
        self.username = username
        self.password = password
        self.host = host
        self.sd_uri = "https://{host}/dvn/api/data-deposit/v1.1/swordv2/service-document".format(host=self.host)
        
        # Connection Status and SWORD Properties
        self.status = None
        self.connected = False
        self.service_document = None
        
        self.connect()

    @property
    def auth(self):
        return (self.token, None) if self.token else (self.username, self.password)

    @property
    def has_api_key(self):
        return True if self.token else False

    def connect(self):
        resp = requests.get(self.sd_uri, auth=self.auth)

        if resp.status_code == 403:
            raise UnauthorizedError('The credentials provided are invalid.')
        elif resp.status_code != 200:
            raise DataverseError('Could not connect to the Dataverse')

        self.connected = True
        self.service_document = etree.XML(resp.content)
        
    def get_dataverses(self, refresh=False, allow_root=False):
        if refresh:
            self.connect()

        collections = get_elements(
            self.service_document[0],
            tag="collection",
        )

        # Remove root Dataverses, which may cause permission issues
        # See https://github.com/IQSS/dataverse/issues/1070
        if not allow_root:
            collections = filter(is_not_root_dataverse, collections)
        
        return [Dataverse(self, col) for col in collections]

    def get_dataverse(self, alias):
        return next((dataverse for dataverse in self.get_dataverses()
                     if dataverse.alias == alias), None)
