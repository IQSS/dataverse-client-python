from __future__ import absolute_import

from dataverse.utils import sanitize


class DataverseFile(object):
    def __init__(self, dataset, name, file_id=None):
        self.dataset = dataset
        self.name = sanitize(name)
        self.id = file_id

        self.download_url = '{0}/access/datafile/{1}'.format(
            dataset.connection.native_base_url, self.id
        )
        edit_media_base = '{0}/edit-media/file/{1}'
        self.edit_media_uri = edit_media_base.format(
            dataset.connection.sword_base_url, self.id
        )

    @classmethod
    def from_json(cls, dataset, json):
        name = json['datafile']['name']
        file_id = json['datafile']['id']
        return cls(dataset, name, file_id)
