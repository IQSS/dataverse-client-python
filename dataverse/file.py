import urlparse

from exceptions import InsufficientMetadataError
from utils import get_element, sanitize


class DataverseFile(object):
    def __init__(self, dataset, name, file_id=None, edit_media_uri=None):
        self.dataset = dataset
        self.name = sanitize(name)

        if edit_media_uri:
            self.is_published = False
            self.edit_media_uri = edit_media_uri
            self.id = edit_media_uri.split('/')[-2]
            self.download_url = 'http://{0}/api/access/datafile/{1}'.format(
                dataset.connection.host, self.id
            )
        elif file_id:
            self.is_published = True
            self.id = file_id
            self.download_url = 'http://{0}/api/access/datafile/{1}'.format(
                dataset.connection.host, self.id
            )
        else:
            raise InsufficientMetadataError(
                'Files must have a file id or edit media uri.'
            )

    @classmethod
    def from_statement(cls, dataset, element):
        edit_media_uri = get_element(element, 'content').get('src')
        name = edit_media_uri.rsplit("/", 1)[-1]
        return cls(dataset, name, edit_media_uri=edit_media_uri)

    @classmethod
    def from_json(cls, dataset, json):
        name = json['datafile']['name']
        file_id = json['datafile']['id']
        return cls(dataset, name, file_id)