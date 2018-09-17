from __future__ import absolute_import

import os
import json

try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO

from zipfile import ZipFile

from lxml import etree
import requests

from .exceptions import (
    NoContainerError, OperationFailedError, UnpublishedDataverseError,
    ConnectionError, MetadataNotFoundError, VersionJsonNotFoundError,
)
from dataverse.file import DataverseFile
from dataverse.settings import SWORD_BOOTSTRAP
from dataverse.utils import get_element, get_files_in_path, add_field


class Dataset(object):
    def __init__(self, entry=SWORD_BOOTSTRAP, dataverse=None, edit_uri=None,
                 edit_media_uri=None, statement_uri=None, **kwargs):
        """
        Datasets must have a title, description, and author.
        This can be specified in the atom entry or as kwargs
        """
        self.dataverse = dataverse

        self.edit_uri = edit_uri
        self.edit_media_uri = edit_media_uri
        self.statement_uri = statement_uri
        self.is_deleted = False

        self._entry = etree.XML(entry) if isinstance(entry, str) else entry
        self._statement = None
        self._metadata = {}
        self._id = None

        # Updates sword entry from keyword arguments
        for key in kwargs:
            value = kwargs[key]
            if isinstance(value, list):
                for item in value:
                    add_field(self._entry, key, item, 'dcterms')
            else:
                add_field(self._entry, key, value, 'dcterms')

        self.title = get_element(
            self._entry, tag='title', namespace='dcterms'
        ).text

    @classmethod
    def from_xml_file(cls, xml_file):
        with open(xml_file) as f:
            xml = f.read()
        return cls(xml)

    @classmethod
    def from_dataverse(cls, entry_element, dataverse):

        # Entry not in appropriate format--extract relevant metadata
        id_element = get_element(entry_element, tag='id')
        title_element = get_element(entry_element, tag='title')
        edit_media_element = get_element(
            entry_element,
            tag='link',
            attribute='rel',
            attribute_value='edit-media',
        )

        return cls(
            title=title_element.text,
            id=id_element.text,
            dataverse=dataverse,
            edit_uri=entry_element.base,
            edit_media_uri=edit_media_element.get('href'),
        )

    @property
    def doi(self):
        if not self.dataverse:
            raise NoContainerError('This dataset has not been added to a Dataverse.')

        # Note: This depends strongly on URL structure, and may break easily
        return self.edit_media_uri.rsplit('/study/', 1)[-1]

    @property
    def id(self):
        if self._id:
            return self._id

        if not self.dataverse:
            raise NoContainerError('This dataset has not been added to a Dataverse.')

        for dataset in self.dataverse.get_contents(refresh=True):
            doi = '{0}:{1}/{2}'.format(
                dataset['protocol'],
                dataset['authority'],
                dataset['identifier'],
            )
            if doi == self.doi:
                self._id = dataset['id']
                return self._id

        raise MetadataNotFoundError('The dataset ID could not be found.')

    @property
    def citation(self):
        return get_element(
            self.get_entry(),
            namespace='http://purl.org/dc/terms/',
            tag='bibliographicCitation'
        ).text

    @property
    def connection(self):
        return self.dataverse.connection if self.dataverse else None

    def get_entry(self, refresh=False):
        if not refresh and self._entry is not None:
            return etree.tostring(self._entry)

        resp = requests.get(self.edit_uri, auth=self.connection.auth)

        if resp.status_code != 200:
            raise ConnectionError('Atom entry could not be retrieved.')

        entry_string = resp.content
        self._entry = etree.XML(entry_string)
        return entry_string

    def get_statement(self, refresh=False):
        if not refresh and self._statement:
            return self._statement

        if not self.dataverse:
            raise NoContainerError('This dataset has not been added to a Dataverse.')

        if not self.statement_uri:
            # Try to find statement uri without a request to the server
            link = get_element(
                self.get_entry(),
                tag='link',
                attribute='rel',
                attribute_value='http://purl.org/net/sword/terms/statement',
            )
            if link is None:
                # Find link with request to server
                link = get_element(
                    self.get_entry(refresh=True),
                    tag='link',
                    attribute='rel',
                    attribute_value='http://purl.org/net/sword/terms/statement',
                )
            self.statement_uri = link.get('href')

        resp = requests.get(self.statement_uri, auth=self.connection.auth)

        if resp.status_code != 200:
            raise ConnectionError('Statement could not be retrieved.')

        self._statement = resp.content
        return self._statement

    def get_state(self, refresh=False):
        if self.is_deleted:
            return 'DEACCESSIONED'

        return get_element(
            self.get_statement(refresh),
            tag='category',
            attribute='term',
            attribute_value='latestVersionState'
        ).text

    def get_metadata(self, version='latest', refresh=False):
        if not refresh and self._metadata.get(version):
            return self._metadata[version]

        if not self.dataverse:
            raise NoContainerError('This dataset has not been added to a Dataverse.')

        url = '{0}/datasets/{1}/versions/:{2}'.format(
            self.connection.native_base_url,
            self.id,
            version,
        )

        resp = requests.get(url, params={'key': self.connection.token})

        if resp.status_code == 404:
            raise VersionJsonNotFoundError(
                'JSON metadata could not be found for this version.'
            )
        elif resp.status_code != 200:
            raise ConnectionError('JSON metadata could not be retrieved.')

        metadata = resp.json()['data']
        self._metadata[version] = metadata

        # Update corresponding version metadata if retrieving 'latest'
        if version == 'latest':
            latest_version = (
                'latest-published'
                if metadata['versionState'] == 'RELEASED'
                else 'draft'
            )
            self._metadata[latest_version] = metadata

        return metadata

    def update_metadata(self, metadata):
        """Updates dataset draft with provided metadata.
        Will create a draft version if none exists.

        :param dict metadata: json retrieved from `get_version_metadata`
        """
        url = '{0}/datasets/{1}/versions/:draft'.format(
            self.connection.native_base_url,
            self.id,
        )
        resp = requests.put(
            url,
            headers={'Content-type': 'application/json'},
            data=json.dumps(metadata),
            params={'key': self.connection.token},
        )

        if resp.status_code != 200:
            raise OperationFailedError('JSON metadata could not be updated.')

        updated_metadata = resp.json()['data']
        self._metadata['draft'] = updated_metadata
        self._metadata['latest'] = updated_metadata

    def create_draft(self):
        """Create draft version of dataset without changing metadata"""
        metadata = self.get_metadata(refresh=True)
        if metadata.get('versionState') == 'RELEASED':
            self.update_metadata(metadata)

    def publish(self):
        if not self.dataverse.is_published:
            raise UnpublishedDataverseError('Host Dataverse must be published.')

        resp = requests.post(
            self.edit_uri,
            headers={'In-Progress': 'false', 'Content-Length': '0'},
            auth=self.connection.auth,
        )

        if resp.status_code != 200:
            raise OperationFailedError('The Dataset could not be published.')

        self._metadata.pop('draft', None)
        self._refresh(receipt=resp.content)

    def get_file(self, file_name, version='latest', refresh=False):
        files = self.get_files(version, refresh)
        return next((f for f in files if f.name == file_name), None)

    def get_file_by_id(self, file_id, version='latest', refresh=False):
        files = self.get_files(version, refresh)
        return next((f for f in files if f.id == file_id), None)

    def get_files(self, version='latest', refresh=False):
        try:
            files_json = self.get_metadata(version, refresh)['files']
            return [DataverseFile.from_json(self, file_json)
                    for file_json in files_json]
        except VersionJsonNotFoundError:
            return []

    def upload_filepath(self, filepath):
        self.upload_filepaths([filepath])

    def upload_filepaths(self, filepaths):
        # Convert a directory to a list of files
        if len(filepaths) == 1 and os.path.isdir(filepaths[0]):
            filepaths = get_files_in_path(filepaths[0])

        # Zip up files
        s = StringIO()
        zip_file = ZipFile(s, 'w')
        for filepath in filepaths:
            zip_file.write(filepath)
        zip_file.close()
        content = s.getvalue()

        self.upload_file('temp.zip', content, zip_files=False)

    def upload_file(self, filename, content, zip_files=True):
        if zip_files:
            s = StringIO()
            zip_file = ZipFile(s, 'w')
            zip_file.writestr(filename, content)
            zip_file.close()
            # filename, content should reflect zipped file
            filename = 'temp.zip'
            content = s.getvalue()

        headers = {
            'Content-Disposition': 'filename={0}'.format(filename),
            'Content-Type': 'application/zip',
            'Packaging': 'http://purl.org/net/sword/package/SimpleZip',
        }

        requests.post(
            self.edit_media_uri,
            data=content,
            headers=headers,
            auth=self.connection.auth,
        )

        self.get_metadata(refresh=True)
        # Note: We can't determine which file was uploaded. Returns None

    def delete_file(self, dataverse_file):
        resp = requests.delete(
            dataverse_file.edit_media_uri,
            auth=self.connection.auth,
        )

        if resp.status_code != 204:
            raise OperationFailedError('The file could not be deleted.')

        self.get_metadata(refresh=True)

    # If we perform a server operation, we should refresh the dataset object
    def _refresh(self, receipt=None):
        if receipt:
            self.edit_uri = get_element(
                receipt,
                tag='link',
                attribute='rel',
                attribute_value='edit'
            ).get('href')
            self.edit_media_uri = get_element(
                receipt,
                tag='link',
                attribute='rel',
                attribute_value='edit-media'
            ).get('href')
            self.statement_uri = get_element(
                receipt,
                tag='link',
                attribute='rel',
                attribute_value='http://purl.org/net/sword/terms/statement'
            ).get('href')

        self.get_statement(refresh=True)
        self.get_entry(refresh=True)
        self.get_metadata('latest', refresh=True)
