import os
import StringIO
from zipfile import ZipFile

from lxml import etree
import requests

from exceptions import (
    NoContainerError, OperationFailedError,
    ConnectionError, MetadataNotFoundError, VersionJsonNotFoundError
)
from file import DataverseFile
from settings import SWORD_BOOTSTRAP
from utils import get_element, get_files_in_path, add_field


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

        self._entry = etree.XML(entry) if isinstance(entry, str) else entry
        self._statement = None
        self._state = None
        self._json = {}
        self._id = None

        # Updates sword entry from keyword arguments
        for key, value in kwargs.iteritems():
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
        id_element = get_element(entry_element, tag="id")
        title_element = get_element(entry_element, tag="title")
        edit_media_element = get_element(
            entry_element,
            tag="link",
            attribute="rel",
            attribute_value="edit-media",
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
        return self.edit_media_uri.rsplit("/study/", 1)[-1]

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
            tag="bibliographicCitation"
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
                tag="link",
                attribute="rel",
                attribute_value="http://purl.org/net/sword/terms/statement",
            )
            if link is None:
                # Find link with request to server
                link = get_element(
                    self.get_entry(refresh=True),
                    tag="link",
                    attribute="rel",
                    attribute_value="http://purl.org/net/sword/terms/statement",
                )
            self.statement_uri = link.get("href")

        resp = requests.get(self.statement_uri, auth=self.connection.auth)

        if resp.status_code != 200:
            raise ConnectionError('Statement could not be retrieved.')

        self._statement = resp.content
        return self._statement

    def get_state(self, refresh=False):
        if not refresh and self._state or self._state == 'DEACCESSIONED':
            return self._state

        self._state = get_element(
            self.get_statement(refresh),
            tag="category",
            attribute="term",
            attribute_value="latestVersionState"
        ).text
        return self._state

    def get_json(self, version="latest", refresh=False):
        if not refresh and self._json.get(version):
            return self._json.get(version)

        if not self.dataverse:
            raise NoContainerError('This dataset has not been added to a Dataverse.')

        json_url = 'https://{0}/api/datasets/{1}/versions/:{2}'.format(
            self.connection.host,
            self.id,
            version,
        )

        resp = requests.get(json_url, params={'key': self.connection.token})

        if resp.status_code == 404:
            raise VersionJsonNotFoundError('JSON metadata could not be found for this version.')
        elif resp.status_code != 200:
            raise ConnectionError('JSON metadata could not be retrieved.')

        self._json[version] = resp.json()['data']
        return self._json[version]

    def get_file(self, file_name, version="latest", refresh=True):
        files = self.get_files(version, refresh)
        return next((f for f in files if f.name == file_name), None)

    def get_file_by_id(self, file_id, version="latest", refresh=True):
        files = self.get_files(version, refresh)
        return next((f for f in files if f.id == file_id), None)

    def get_files(self, version="latest", refresh=True):
        try:
            files_json = self.get_json(version, refresh)['files']
            return [DataverseFile.from_json(self, file_json)
                    for file_json in files_json]
        except VersionJsonNotFoundError:
            return []

    def add_file(self, filepath):
        self.add_files([filepath])

    def add_files(self, filepaths):
        # Convert a directory to a list of files
        if len(filepaths) == 1 and os.path.isdir(filepaths[0]):
            filepaths = get_files_in_path(filepaths[0])

        # Zip up files
        s = StringIO.StringIO()
        zip_file = ZipFile(s, 'w')
        for filepath in filepaths:
            zip_file.write(filepath)
        zip_file.close()
        content = s.getvalue()

        self.upload_file('temp.zip', content, zip=False)

    def upload_file(self, filename, content, zip=True):
        if zip:
            s = StringIO.StringIO()
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

        self._refresh()

    def publish(self):
        resp = requests.post(
            self.edit_uri,
            headers={'In-Progress': 'false', 'Content-Length': 0},
            auth=self.connection.auth,
        )

        if resp.status_code != 200:
            raise OperationFailedError('The Dataverse could not be published.')

        receipt = resp.content
        self._refresh(receipt=receipt)
    
    def delete_file(self, dataverse_file):
        resp = requests.delete(
            dataverse_file.edit_media_uri,
            auth=self.connection.auth,
        )

        if resp.status_code != 204:
            raise OperationFailedError('The file could not be deleted.')
        
    def delete_all_files(self):
        for f in self.get_files():
            self.delete_file(f)

    # TODO: DANGEROUS! Will delete all unspecified fields! Deposit receipts only give SOME of the fields
    # Can potentially be replaced with native API functionality
    # def update_metadata(self):
    #     depositReceipt = self.hostDataverse.connection.sword.update(
    #         dr=self.lastDepositReceipt,
    #         edit_iri=self.editUri,
    #         edit_media_iri=self.editMediaUri,
    #         metadata_entry=self.entry,
    #     )
    #     self._refresh(deposit_receipt=depositReceipt)

    # if we perform a server operation, we should refresh the dataset object
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
        self.get_state(refresh=True)
