from lxml import etree
import requests

from dataverse import Dataverse
from utils import get_elements


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

    def connect(self):
        resp = requests.get(self.sd_uri, auth=self.auth)
        self.status = resp.status_code
        self.connected = True if self.status == 200 else False
        self.service_document = etree.XML(resp.content)
        
    def get_dataverses(self):
        # Get latest dataverse information
        self.connect()

        # Dataverse 4.0 beta currently returns collection for "Harvard" DV,
        # which the user may not have permissions on. Could cause problems.
        collections = get_elements(
            self.service_document[0],
            tag="collection",
        )

        return [Dataverse(self, col) for col in collections]

    def get_dataverse(self, alias):
        return next((dataverse for dataverse in self.get_dataverses()
                     if dataverse.alias == alias), None)
