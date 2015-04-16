from lxml import etree
import requests

from dataverse import Dataverse
from exceptions import UnauthorizedError, ConnectionError
from utils import get_elements


class Connection(object):

    def __init__(self, host, token):
        # Connection Properties
        self.token = token
        self.host = host
        self.sd_uri = "https://{host}/dvn/api/data-deposit/v1.1/swordv2/service-document".format(host=self.host)
        self.service_document = None
        
        self.connect()

    @property
    def auth(self):
        return self.token, None

    def connect(self):
        resp = requests.get(self.sd_uri, auth=self.auth)

        if resp.status_code == 403:
            raise UnauthorizedError('The credentials provided are invalid.')
        elif resp.status_code != 200:
            raise ConnectionError('Could not connect to the Dataverse')

        self.service_document = etree.XML(resp.content)
        
    def get_dataverses(self, refresh=False):
        if refresh:
            self.connect()

        collections = get_elements(
            self.service_document[0],
            tag="collection",
        )
        
        return [Dataverse(self, col) for col in collections]

    def get_dataverse(self, alias, refresh=False):
        return next((dataverse for dataverse in self.get_dataverses(refresh)
                     if dataverse.alias == alias), None)
