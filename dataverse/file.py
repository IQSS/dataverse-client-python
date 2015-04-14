from utils import sanitize


class DataverseFile(object):
    def __init__(self, dataset, name, file_id=None, edit_media_uri=None):
        self.dataset = dataset
        self.name = sanitize(name)
        self.id = file_id

        self.download_url = 'http://{0}/api/access/datafile/{1}'.format(
            dataset.connection.host, self.id
        )
        self.edit_media_uri = 'https://{0}/dvn/api/data-deposit/v1.1/swordv2/edit-media/file/{1}'.format(
            dataset.connection.host, self.id
        )

    @classmethod
    def from_json(cls, dataset, json):
        name = json['datafile']['name']
        file_id = json['datafile']['id']
        return cls(dataset, name, file_id)