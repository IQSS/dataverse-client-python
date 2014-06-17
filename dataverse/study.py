# python base lib modules
import os
import pprint
import StringIO
from zipfile import ZipFile

# downloaded modules
import sword2
import requests

# local modules
from file import DataverseFile
from utils import format_term, get_element, get_elements, DataverseException, \
    get_files_in_path, sanitize


class Study(object):
    def __init__(self, entry=None, title=None, dataverse=None, edit_uri=None,
                 edit_media_uri=None, statement_uri=None, **kwargs):

        # Generate sword entry
        sword_entry = sword2.Entry(entry)
        if not get_elements(sword_entry.pretty_print(), namespace='dcterms', tag='title'):
            # Append title to entry
            if isinstance(title, basestring):
                sword_entry.add_field(format_term('title'), title)
            else:
                raise DataverseException('Study needs a single, valid title.')
        if kwargs:
            # Updates sword entry from keyword arguments
            for k in kwargs.keys():
                if isinstance(kwargs[k], list):
                    for item in kwargs[k]:
                        sword_entry.add_field(format_term(k), item)
                else:
                    sword_entry.add_field(format_term(k), kwargs[k])

        self.entry = sword_entry.pretty_print()
        self.dataverse = dataverse

        self.edit_uri = edit_uri
        self.edit_media_uri = edit_media_uri
        self.statement_uri = statement_uri

    def __repr__(self):
        studyObject = pprint.pformat(self.__dict__)
        entryObject = self.entry
        return """STUDY ========= "
        study=
{so}
        
        entry=
{eo}
/STUDY ========= """.format(so=studyObject, eo=entryObject)

    @classmethod
    def from_xml_file(cls, xml_file):
        with open(xml_file) as f:
            xml = f.read()
        return cls(xml)

    @classmethod
    def from_entry(cls, entry_element, dataverse=None):

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
    def title(self):
        dirty_title = get_element(self.get_statement(), tag='title').text
        return sanitize(dirty_title)

    @property
    def doi(self):
        url_pieces = self.edit_media_uri.rsplit("/")
        return '/'.join([url_pieces[-3], url_pieces[-2], url_pieces[-1]])

    @property
    def citation(self):
        return get_element(
            self.get_entry(),
            namespace='http://purl.org/dc/terms/',
            tag="bibliographicCitation"
        ).text

    def get_entry(self):
        return self.dataverse.connection.sword.get_resource(self.edit_uri).content

    def get_statement(self):
        if not self.statement_uri:
            entry = self.get_entry()
            link = get_element(
                entry,
                tag="link",
                attribute="rel",
                attribute_value="http://purl.org/net/sword/terms/statement",
            )
            self.statement_uri = link.get("href")

        statement = self.dataverse.connection.sword.get_resource(self.statement_uri).content
        return statement

    def get_state(self):
        return get_element(
            self.get_statement(),
            tag="category",
            attribute="term",
            attribute_value="latestVersionState"
        ).text

    def get_file(self, file_name, released=False):

        # Search released study if specified; otherwise, search draft
        files = self.get_released_files() if released else self.get_files()
        return next((f for f in files if f.name == file_name), None)

    def get_file_by_id(self, file_id, released=False):

        # Search released study if specified; otherwise, search draft
        files = self.get_released_files() if released else self.get_files()
        return next((f for f in files if f.id == file_id), None)

    def get_files(self, released=False):
        if released:
            return self.get_released_files()

        sword_statement = sword2.Atom_Sword_Statement(self.get_statement())
        return [DataverseFile.from_statement(resource, self)
                for resource in sword_statement.resources]

    def get_released_files(self):
        """
        Uses data sharing API to retrieve a list of files from the most
        recently released version of the study
        """
        metadata_url = 'https://{0}/dvn/api/metadata/{1}'.format(
            self.dataverse.connection.host, self.doi
        )
        xml = requests.get(metadata_url, verify=False).content
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
            filename = os.path.basename(filepath)
            if os.path.getsize(filepath) < 5:
                raise DataverseException('The Dataverse does not currently accept files less than 5 bytes. '
                                   '{} cannot be uploaded.'.format(filename))
            elif filename in [f.name for f in self.get_files()]:
                raise DataverseException('The file {} already exists on the Dataverse'.format(filename))
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
            verify=False,
            auth=(self.dataverse.connection.username,
                  self.dataverse.connection.password),
        )

        self._refresh()

    def release(self):
        receipt = self.dataverse.connection.sword.complete_deposit(
            se_iri=self.edit_uri,
        )
        self._refresh(receipt=receipt)
    
    def delete_file(self, dataverse_file):
        if dataverse_file.is_released:
            raise DataverseException(
                'Released versions of files cannot be deleted.'
            )

        receipt = self.dataverse.connection.sword.delete_file(
            dataverse_file.edit_media_uri
        )
        # Dataverse does not give a desposit receipt at this time
        self._refresh(receipt=None)
        
    def delete_all_files(self):
        for f in self.get_files():
            self.delete_file(f)

    # TODO: DANGEROUS! Will delete all unspecified fields! Deposit receipts only give SOME of the fields
    # def update_metadata(self):
    #     #todo: consumer has to use the methods on self.entry (from sword2.atom_objects) to update the
    #     # metadata before calling this method. that's a little cumbersome...
    #     depositReceipt = self.hostDataverse.connection.sword.update(
    #         dr=self.lastDepositReceipt,
    #         edit_iri=self.editUri,
    #         edit_media_iri=self.editMediaUri,
    #         metadata_entry=self.entry,
    #     )
    #     self._refresh(deposit_receipt=depositReceipt)

    # if we perform a server operation, we should refresh the study object
    def _refresh(self, receipt=None):
        # todo is it possible for the deposit receipt to have different info than the study?
        if receipt:
            self.edit_uri = receipt.edit
            self.edit_media_uri = receipt.edit_media
            self.statement_uri = receipt.atom_statement_iri
        self.entry = self.get_entry()
