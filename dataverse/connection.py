from lxml import etree
import requests

from .dataverse import Dataverse
from . import exceptions
from .utils import get_elements


class Connection(object):

    def __init__(self, host, token):
        self.token = token
        self.host = host
        self.sd_uri = 'https://{host}/dvn/api/data-deposit/v1.1/swordv2/service-document'.format(host=self.host)
        self._service_document = None

        self.get_service_document()

    @property
    def auth(self):
        return self.token, None

    def get_service_document(self, refresh=False):
        if not refresh and self._service_document is not None:
            return self._service_document

        resp = requests.get(self.sd_uri, auth=self.auth)

        if resp.status_code == 403:
            raise exceptions.UnauthorizedError('The credentials provided are invalid.')
        elif resp.status_code != 200:
            raise exceptions.ConnectionError('Could not connect to the Dataverse')

        self._service_document = etree.XML(resp.content)
        return self._service_document

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

        self.get_service_document(refresh=True)
        return self.get_dataverse(alias)

    def delete_dataverse(self, dataverse):

        resp = requests.delete(
            'https://{0}/api/dataverses/{1}'.format(self.host, dataverse.alias),
            params={'key': self.token},
        )

        if resp.status_code == 401:
            raise exceptions.UnauthorizedError('Delete Dataverse unauthorized.')
        elif resp.status_code == 404:
            raise exceptions.DataverseNotFoundError('Dataverse {0} was not found.'.format(dataverse.alias))
        elif resp.status_code != 200:
            raise exceptions.OperationFailedError('Dataverse {0} could not be deleted.'.format(dataverse.alias))

        self.get_service_document(refresh=True)

    def get_dataverses(self, refresh=False):
        collections = get_elements(
            self.get_service_document(refresh)[0],
            tag='collection',
        )

        return [Dataverse(self, col) for col in collections]

    def get_dataverse(self, alias, refresh=False):
        return next((dataverse for dataverse in self.get_dataverses(refresh)
                     if dataverse.alias == alias), None)
