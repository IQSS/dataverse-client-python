import requests

from study import Study
from utils import get_element, get_elements, DataverseException, sanitize


class Dataverse(object):
    def __init__(self, connection, collection):
        self.connection = connection
        self.collection = collection

    @property
    def is_released(self):

        collection_info = requests.get(
            self.collection.get('href'),
            auth=self.connection.auth,
        ).content

        status = get_element(
            collection_info,
            namespace="http://purl.org/net/sword/terms/state",
            tag="dataverseHasBeenReleased",
        ).text

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

    def release(self):
        edit_uri = 'https://{0}/dvn/api/data-deposit/v1.1/swordv2/edit/dataverse/{1}'.format(
            self.connection.host, self.alias
        )
        resp = requests.post(
            edit_uri,
            headers={'In-Progress': 'false'},
            auth=self.connection.auth,
        )

        if resp.status_code != 200:
            raise DataverseException('The Dataverse could not be released.')

    def add_study(self, study):

        if get_element(study._entry, 'title', 'dcterms') is None:
            raise DataverseException('This study must have a title.')
        if get_element(study._entry, 'description', 'dcterms') is None:
            raise DataverseException('This study must have a description.')
        if get_element(study._entry, 'creator', 'dcterms') is None:
            raise DataverseException('This study must have an author.')

        resp = requests.post(
            self.collection.get('href'),
            data=study.get_entry(),
            headers={'Content-type': 'application/atom+xml'},
            auth=self.connection.auth,
        )

        if resp.status_code != 201:
            raise DataverseException('This study could not be added.')

        study.dataverse = self
        study._refresh(receipt=resp.content)
        
    def delete_study(self, study):

        if study._state == 'DELETED' or study._state == 'DEACCESSIONED':
            raise DataverseException('This study has already been deleted.')

        resp = requests.delete(
            study.edit_uri,
            auth=self.connection.auth,
        )
        if resp.status_code == 405:
            raise DataverseException('Released studies can only be deleted '
                'from the GUI. For more information, please refer to '
                'https://github.com/IQSS/dataverse/issues/778')

        study._state = 'DEACCESSIONED'
        
    def get_studies(self):

        collection_info = requests.get(
            self.collection.get('href'),
            auth=self.connection.auth,
        ).content

        entries = get_elements(collection_info, tag='entry')
        return [Study.from_dataverse(entry, self) for entry in entries]

    def get_study_by_doi(self, doi):
        return next((s for s in self.get_studies() if s.doi == doi), None)

    def get_study_by_title(self, title):
        return next((s for s in self.get_studies() if s.title == title), None)

    def get_study_by_string_in_entry(self, string):
        return next((s for s in self.get_studies() if string in s.get_entry()), None)
