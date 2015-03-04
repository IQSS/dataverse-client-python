import requests

from dataset import Dataset
from exceptions import (
    InsufficientMetadataError, MethodNotAllowedError, OperationFailedError,
)
from utils import get_element, get_elements, sanitize


class Dataverse(object):
    def __init__(self, connection, collection):
        self.connection = connection
        self.collection = collection

    @property
    def is_published(self):

        collection_info = requests.get(
            self.collection.get('href'),
            auth=self.connection.auth,
        ).content

        status_tag = get_element(
            collection_info,
            namespace="http://purl.org/net/sword/terms/state",
            tag="dataverseHasBeenReleased",
        )
        status = status_tag.text

        return status.lower() == 'true'

    @property
    def alias(self):
        return self.collection.get('href').split('/')[-1]

    @property
    def title(self):
        return sanitize(get_element(
            self.collection,
            namespace='atom',
            tag='title',
        ).text)

    def publish(self):
        edit_uri = 'https://{0}/dvn/api/data-deposit/v1.1/swordv2/edit/dataverse/{1}'.format(
            self.connection.host, self.alias
        )
        resp = requests.post(
            edit_uri,
            headers={'In-Progress': 'false'},
            auth=self.connection.auth,
        )

        if resp.status_code != 200:
            raise OperationFailedError('The Dataverse could not be published.')

    def add_dataset(self, dataset):
        if get_element(dataset._entry, 'title', 'dcterms') is None:
            raise InsufficientMetadataError('This dataset must have a title.')
        if get_element(dataset._entry, 'description', 'dcterms') is None:
            raise InsufficientMetadataError('This dataset must have a description.')
        if get_element(dataset._entry, 'creator', 'dcterms') is None:
            raise InsufficientMetadataError('This dataset must have an author.')

        resp = requests.post(
            self.collection.get('href'),
            data=dataset.get_entry(),
            headers={'Content-type': 'application/atom+xml'},
            auth=self.connection.auth,
        )

        if resp.status_code != 201:
            raise OperationFailedError('This dataset could not be added.')

        dataset.dataverse = self
        dataset._refresh(receipt=resp.content)
        
    def delete_dataset(self, dataset):
        if dataset._state == 'DELETED' or dataset._state == 'DEACCESSIONED':
            return

        resp = requests.delete(
            dataset.edit_uri,
            auth=self.connection.auth,
        )
        if resp.status_code == 405:
            raise MethodNotAllowedError('Published datasets can only be '
                'deleted from the GUI. For more information, please refer to '
                'https://github.com/IQSS/dataverse/issues/778')

        dataset._state = 'DEACCESSIONED'
        
    def get_datasets(self):

        collection_info = requests.get(
            self.collection.get('href'),
            auth=self.connection.auth,
        ).content

        entries = get_elements(collection_info, tag='entry')
        return [Dataset.from_dataverse(entry, self) for entry in entries]

    def get_dataset_by_doi(self, doi):
        return next((s for s in self.get_datasets() if s.doi == doi), None)

    def get_dataset_by_title(self, title):
        return next((s for s in self.get_datasets() if s.title == title), None)

    def get_dataset_by_string_in_entry(self, string):
        return next((s for s in self.get_datasets() if string in s.get_entry()), None)
