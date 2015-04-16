from lxml import etree
import requests

from dataverse import Dataverse
import exceptions
from utils import get_elements


class Connection(object):

    def __init__(self, host, token):
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
            raise exceptions.UnauthorizedError('The credentials provided are invalid.')
        elif resp.status_code != 200:
            raise exceptions.ConnectionError('Could not connect to the Dataverse')

        self.service_document = etree.XML(resp.content)

    def create_dataverse(self, alias, name, email, parent=':root'):
        resp = requests.post(
            'https://{0}/api/dataverses/{1}'.format(self.host, parent),
            json={
                'alias': alias,
                'name': name,
                'dataverseContacts': [{'contactEmail': email}],
            },
            params={'key': self.token},
        )

        if resp.status_code == 404:
            raise exceptions.DataverseNotFoundError('Dataverse {0} was not found.'.format(parent))
        elif resp.status_code != 201:
            raise exceptions.OperationFailedError('{0} Dataverse could not be created.'.format(name))

    def delete_dataverse(self, alias):
        resp = requests.delete(
            'https://{0}/api/dataverses/{1}'.format(self.host, alias),
            params={'key': self.token},
        )

        if resp.status_code == 401:
            raise exceptions.UnauthorizedError('Delete Dataverse unauthorized.')
        elif resp.status_code == 404:
            raise exceptions.DataverseNotFoundError('Dataverse {0} was not found.'.format(alias))
        elif resp.status_code != 200:
            raise exceptions.OperationFailedError('Dataverse {0} could not be deleted.'.format(alias))

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
