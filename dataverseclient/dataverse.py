# python base lib modules

# downloaded modules
from lxml import etree

# local modules
from study import Study
import utils

class Dataverse(object):
    def __init__(self, connection, collection):
        self.connection = connection
        self.collection = collection

    # Note: is_released is a Dataverse concept--not from SWORD
    @property
    def is_released(self):
        # Get entry resource for collection
        collection_info = self.connection.swordConnection.get_resource(self.collection.href).content
        status = utils.get_element(
            collection_info,
            namespace="http://purl.org/net/sword/terms/state",
            tag="dataverseHasBeenReleased",
        ).text
        return status.lower() == 'true'

    @property
    def alias(self):
        return self.collection.href.split('/')[-1]

    @property
    def title(self):
        return utils.sanitize(self.collection.title)

    def add_study(self, study):
        # this creates the study AND generates a deposit receipt
        receipt = self.connection.swordConnection.create(
            col_iri=self.collection.href,
            metadata_entry=study.entry,
        )
                                                     
        study.dataverse = self
        study._refresh(receipt=receipt)
        
    def delete_study(self, study):
        # Receipt won't contain any information.
        receipt = self.connection.swordConnection.delete(study.edit_uri)
        
    def get_studies(self):
        response = self.connection.swordConnection.get_resource(self.collection.href)
        entries = utils.get_elements(response.content, tag='entry')
        return [Study.from_entry(entry, dataverse=self) for entry in entries]

    def get_study_by_doi(self, doi):
        return next((s for s in self.get_studies() if s.doi == doi), None)

    def get_study_by_title(self, title):
        return next((s for s in self.get_studies() if s.title == title), None)

    def get_study_by_string_in_entry(self, string):
        return next((s for s in self.get_studies() if string in s.entry), None)
