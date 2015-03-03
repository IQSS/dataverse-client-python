import os
import StringIO
from zipfile import ZipFile

from lxml import etree
import requests

from file import DataverseFile
from settings import SWORD_BOOTSTRAP
from utils import (
    get_element, get_elements, DataverseException, get_files_in_path,
    add_field,
)


class Dataset(object):
    def __init__(self, entry=SWORD_BOOTSTRAP, dataverse=None, edit_uri=None,
                 edit_media_uri=None, statement_uri=None, **kwargs):
        """
        Datasets must have a title, description, and author.
        This can be specified in the atom entry or as kwargs
        """
        self.dataverse = dataverse
        self._statement = None
        self._state = None

        self.edit_uri = edit_uri
        self.edit_media_uri = edit_media_uri
        self.statement_uri = statement_uri

        self._entry = etree.XML(entry) if isinstance(entry, str) else entry

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
        # Note: This depends strongly on URL structure, and may break easily
        return self.edit_media_uri.rsplit("/study/")[-1]

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
            raise DataverseException('Atom entry could not be retrieved.')

        entry_string = resp.content
        self._entry = etree.XML(entry_string)
        return entry_string

    def get_statement(self, refresh=False):
        if not refresh and self._statement:
            return self._statement

        if not self.connection:
            raise DataverseException('This dataset has not been added to a Dataverse.')

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
            raise DataverseException('Statement could not be retrieved.')

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

    def get_file(self, file_name, published=False):

        # Search published dataset if specified; otherwise, search draft
        files = self.get_published_files() if published else self.get_files()
        return next((f for f in files if f.name == file_name), None)

    def get_file_by_id(self, file_id, published=False):

        # Search published dataset if specified; otherwise, search draft
        files = self.get_published_files() if published else self.get_files()
        return next((f for f in files if f.id == file_id), None)

    def get_files(self, published=False, refresh=True):
        if published:
            return self.get_published_files()

        return [
            DataverseFile.from_statement(resource, self)
            for resource in get_elements(self.get_statement(refresh), 'entry')
        ]

    def get_published_files(self):
        """
        Uses data sharing API to retrieve a list of files from the most
        recently published version of the dataset
        """
        metadata_url = 'https://{0}/dvn/api/metadata/{1}'.format(
            self.connection.host, self.doi
        )
        xml = requests.get(metadata_url, auth=self.connection.auth).content
        elements = get_elements(xml, tag='otherMat')

        return [DataverseFile.from_metadata(element, self)
                for element in elements]

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
            raise DataverseException('The Dataverse could not be published.')

        receipt = resp.content
        self._refresh(receipt=receipt)
    
    def delete_file(self, dataverse_file):
        if dataverse_file.is_published:
            raise DataverseException(
                'Published versions of files cannot be deleted.'
            )

        resp = requests.delete(
            dataverse_file.edit_media_uri,
            auth=self.connection.auth,
        )

        if resp.status_code != 204:
            raise DataverseException('The file could not be deleted.')
        
    def delete_all_files(self):
        for f in self.get_files():
            self.delete_file(f)

    # TODO: DANGEROUS! Will delete all unspecified fields! Deposit receipts only give SOME of the fields
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
