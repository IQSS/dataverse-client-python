import requests

from dataset import Dataset
from exceptions import (
    InsufficientMetadataError, MethodNotAllowedError, OperationFailedError,
    ConnectionError
)
from utils import get_element, get_elements, sanitize


class Dataverse(object):
    def __init__(self, connection, collection):
        self.connection = connection
        self.collection = collection

        self._collection_info = None
        self._contents_json = None

    @property
    def is_published(self):

        # Always check latest version
        collection_info = requests.get(
            self.collection.get('href'),
            auth=self.connection.auth,
        ).content

        status_tag = get_element(
            collection_info,
            namespace='http://purl.org/net/sword/terms/state',
            tag='dataverseHasBeenReleased',
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

    def get_contents(self, refresh=False):
        if not refresh and self._contents_json:
            return self._contents_json

        content_uri = 'https://{0}/api/dataverses/{1}/contents'.format(
            self.connection.host, self.alias
        )
        resp = requests.get(
            content_uri,
            params={'key': self.connection.token}
        )

        if resp.status_code != 200:
            raise ConnectionError('Atom entry could not be retrieved.')

        self._contents_json = resp.json()['data']
        return self._contents_json

    def get_collection_info(self, refresh=False):
        if not refresh and self._collection_info:
            return self._collection_info

        self._collection_info = requests.get(
            self.collection.get('href'),
            auth=self.connection.auth,
        ).content
        return self._collection_info

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
        self.get_collection_info(refresh=True)

    def delete_dataset(self, dataset):
        if dataset._state == 'DELETED' or dataset._state == 'DEACCESSIONED':
            return

        resp = requests.delete(
            dataset.edit_uri,
            auth=self.connection.auth,
        )
        if resp.status_code == 405:
            raise MethodNotAllowedError(
                'Published datasets can only be deleted from the GUI. For '
                'more information, please refer to '
                'https://github.com/IQSS/dataverse/issues/778'
            )

        dataset._state = 'DEACCESSIONED'
        self.get_collection_info(refresh=True)

    def get_datasets(self, refresh=False):
        collection_info = self.get_collection_info(refresh)
        entries = get_elements(collection_info, tag='entry')
        return [Dataset.from_dataverse(entry, self) for entry in entries]

    def get_dataset_by_doi(self, doi, refresh=False):
        return next((s for s in self.get_datasets(refresh) if s.doi == doi), None)

    def get_dataset_by_title(self, title, refresh=False):
        return next((s for s in self.get_datasets(refresh) if s.title == title), None)

    def get_dataset_by_string_in_entry(self, string, refresh=False):
        return next((s for s in self.get_datasets(refresh) if string in s.get_entry()), None)
