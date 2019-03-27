from __future__ import absolute_import

import requests

from dataverse.dataset import Dataset
from dataverse.exceptions import (
    ConnectionError, MethodNotAllowedError, OperationFailedError,
)
from dataverse.utils import get_element, get_elements, sanitize


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
            auth=self.connection.auth,verify=self.connection.verify
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

        content_uri = '{0}/dataverses/{1}/contents'.format(
            self.connection.native_base_url, self.alias
        )
        resp = requests.get(
            content_uri,
            params={'key': self.connection.token},verify=self.connection.verify
        )

        if resp.status_code != 200:
            raise ConnectionError('Atom entry could not be retrieved.')

        self._contents_json = resp.json()['data']
        return self._contents_json

    def get_collection_info(self, refresh=False, timeout=None):
        if not refresh and self._collection_info:
            return self._collection_info

        #print(self.collection.get('href'))
        self._collection_info = requests.get(
<<<<<<< HEAD
            self.collection.get('href'),
=======
            self.collection.get('href').replace("https","http"),
>>>>>>> few fixes
            auth=self.connection.auth,
            timeout=timeout,verify=self.connection.verify
        ).content
        return self._collection_info

    def publish(self):
        edit_uri = '{0}/edit/dataverse/{1}'.format(
            self.connection.sword_base_url, self.alias
        )
        resp = requests.post(
            edit_uri,
            headers={'In-Progress': 'false'},
            auth=self.connection.auth,verify=self.connection.verify
        )

        if resp.status_code != 200:
            raise OperationFailedError('The Dataverse could not be published.')

    def create_dataset(self, title, description, creator, **kwargs):
        dataset = Dataset(
            title=title,
            description=description,
            creator=creator,
            **kwargs
        )

        self._add_dataset(dataset)
        return dataset

    def _add_dataset(self, dataset):

        resp = requests.post(
            self.collection.get('href'),
            data=dataset.get_entry(),
            headers={'Content-type': 'application/atom+xml'},
            auth=self.connection.auth,verify=self.connection.verify
        )

        if resp.status_code != 201:
            raise OperationFailedError('This dataset could not be added.')

        dataset.dataverse = self
        dataset._refresh(receipt=resp.content)
        self.get_collection_info(refresh=True)

    def delete_dataset(self, dataset):
        if dataset.get_state() == 'DELETED' or dataset.get_state() == 'DEACCESSIONED':
            return

        resp = requests.delete(
            dataset.edit_uri,
            auth=self.connection.auth,verify=self.connection.verify
        )
        if resp.status_code == 405:
            raise MethodNotAllowedError(
                'Published datasets can only be deleted from the GUI. For '
                'more information, please refer to '
                'https://github.com/IQSS/dataverse/issues/778'
            )

        dataset.is_deleted = True
        self.get_collection_info(refresh=True)

    def get_datasets(self, refresh=False, timeout=None):
        collection_info = self.get_collection_info(refresh, timeout=timeout)
        entries = get_elements(collection_info, tag='entry')
        return [Dataset.from_dataverse(entry, self) for entry in entries]

    def get_dataset_by_doi(self, doi, refresh=False, timeout=None):
        return next(
            (s for s in self.get_datasets(refresh, timeout=timeout) if s.doi == doi),
            None
        )

    def get_dataset_by_title(self, title, refresh=False, timeout=None):
        return next(
            (s for s in self.get_datasets(refresh, timeout=timeout) if s.title == title),
            None
        )

    def get_dataset_by_string_in_entry(self, string, refresh=False, timeout=None):
        return next(
            (s for s in self.get_datasets(refresh, timeout=timeout) if string in s.get_entry()),
            None
        )
