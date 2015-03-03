import urlparse

from utils import DataverseException, get_element, sanitize


class DataverseFile(object):
    def __init__(self, name, dataset, edit_media_uri=None, download_url=None):
        self.name = sanitize(name)
        self.dataset = dataset

        if edit_media_uri:
            self.is_published = False
            self.edit_media_uri = edit_media_uri
            self.id = edit_media_uri.split('/')[-2]
            host = urlparse.urlparse(edit_media_uri).netloc
            self.download_url = 'http://{0}/api/access/datafile/{1}'.format(
                host, self.id
            )
        elif download_url:
            self.is_published = True
            self.download_url = download_url
            self.id = download_url.split('=')[-1]
        else:
            raise DataverseException(
                'Files must have an edit media uri or download url.'
            )

    def __repr__(self):
        return """
    DATAVERSE FILE:
    Name: {0}
    Id: {1}
    Download URL: {2}
    Status: {3}
    """.format(
            self.name,
            self.id,
            self.download_url,
            'PUBLISHED' if self.is_published else 'DRAFT',
        )

    @classmethod
    def from_statement(cls, element, dataset):
        edit_media_uri = get_element(element, 'content').get('src')
        name = edit_media_uri.rsplit("/")[-1]
        return cls(name, dataset, edit_media_uri=edit_media_uri)

    @classmethod
    def from_metadata(cls, element, dataset):
        name = element[0].text
        download_url = element.attrib.get('URI')
        return cls(name, dataset, download_url=download_url)