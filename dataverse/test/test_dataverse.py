import pytest

import uuid
import httpretty

from dataverse.connection import Connection
from dataverse.dataset import Dataset
from dataverse.settings import TEST_HOST, TEST_TOKEN
from dataverse.test.config import PICS_OF_CATS_DATASET, ATOM_DATASET, EXAMPLE_FILES
from dataverse import exceptions
from dataverse import utils

import logging
logging.basicConfig(level=logging.ERROR)


class TestUtils(object):

    def test_get_element(self):
        with open(ATOM_DATASET) as f:
            entry = f.read()

        # One value
        title = utils.get_element(entry, 'title', 'dcterms').text
        assert title == 'Roasting at Home'

        # Two values
        creator = utils.get_element(entry, 'creator', 'dcterms').text
        assert creator == 'Peets, John'

        # No values
        nonsense = utils.get_element(entry, 'nonsense', 'booga')
        assert nonsense is None

    def test_get_elements(self):
        with open(ATOM_DATASET) as f:
            entry = f.read()

        # One value
        titles = utils.get_elements(entry, 'title', 'dcterms')
        assert len(titles) == 1
        assert titles[0].text == 'Roasting at Home'

        # Two values
        creators = utils.get_elements(entry, 'creator', 'dcterms')
        assert len(creators) == 2
        assert creators[0].text == 'Peets, John'
        assert creators[1].text == 'Stumptown, Jane'

        # No values
        nonsense = utils.get_elements(entry, 'nonsense', 'booga')
        assert nonsense == []

    def test_format_term(self):
        # A term not in the replacement dict
        formatted_term = utils.format_term('title', namespace='dcterms')
        assert formatted_term == '{http://purl.org/dc/terms/}title'

    def test_format_term_replace(self):
        # A term in the replacement dict
        formatted_term = utils.format_term('id', namespace='dcterms')
        assert formatted_term == '{http://purl.org/dc/terms/}identifier'


class TestConnection(object):

    def test_connect(self):
        connection = Connection(TEST_HOST, TEST_TOKEN)

        assert connection.host == TEST_HOST
        assert connection.token == TEST_TOKEN
        assert connection.service_document

    def test_connect_unauthorized(self):
        with pytest.raises(exceptions.UnauthorizedError):
            Connection(TEST_HOST, 'wrong-token')

    @httpretty.activate
    def test_connect_unknown_failure(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://{host}/dvn/api/data-deposit/v1.1/swordv2/service-document'.format(host=TEST_HOST),
            status=400,
        )

        with pytest.raises(exceptions.ConnectionError):
            Connection(TEST_HOST, TEST_TOKEN)

    def test_create_dataverse(self):
        connection = Connection(TEST_HOST, TEST_TOKEN)
        alias = str(uuid.uuid1())   # must be unique
        connection.create_dataverse(
            alias,
            'Test Name',
            'dataverse@example.com',
        )

        dataverse = connection.get_dataverse(alias, True)
        try:
            assert dataverse.alias == alias
            assert dataverse.title == 'Test Name'
        finally:
            connection.delete_dataverse(alias)

    def test_delete_dataverse(self):
        connection = Connection(TEST_HOST, TEST_TOKEN)
        alias = str(uuid.uuid1())   # must be unique
        connection.create_dataverse(
            alias,
            'Test Name',
            'dataverse@example.com',
        )

        connection.delete_dataverse(alias)
        dataverse = connection.get_dataverse(alias, True)

        assert dataverse is None


class TestDataset(object):

    def test_init(self):
        dataset = Dataset(title='My Dataset', publisher='Mr. Pub Lisher')
        title = utils.get_element(
            dataset._entry,
            namespace='dcterms',
            tag='title'
        ).text
        publisher = utils.get_element(
            dataset._entry,
            namespace='dcterms',
            tag='publisher'
        ).text
        assert title == 'My Dataset'
        assert title == dataset.title
        assert publisher == 'Mr. Pub Lisher'

    def test_init_from_xml(self):
        dataset = Dataset.from_xml_file(ATOM_DATASET)
        title = utils.get_element(
            dataset.get_entry(),
            namespace='dcterms',
            tag='title'
        ).text
        publisher = utils.get_element(
            dataset.get_entry(),
            namespace='dcterms',
            tag='rights'
        ).text
        assert title == 'Roasting at Home'
        assert publisher == 'Creative Commons CC-BY 3.0 (unported) http://creativecommons.org/licenses/by/3.0/'


class TestDatasetOperations(object):

    @classmethod
    def setup_class(cls):
        print 'Connecting to Dataverse host at {0}'.format(TEST_HOST)
        cls.connection = Connection(TEST_HOST, TEST_TOKEN)

        print 'Creating test Dataverse'
        cls.alias = str(uuid.uuid1())
        cls.connection.create_dataverse(
            cls.alias,
            'Test Dataverse',
            'dataverse@example.com',
        )
        cls.dataverse = cls.connection.get_dataverse(cls.alias, True)
        assert cls.dataverse

    @classmethod
    def teardown_class(cls):

        print 'Removing test Dataverse'
        cls.connection.delete_dataverse(cls.alias)
        dataverse = cls.connection.get_dataverse(cls.alias, True)
        assert dataverse is None

    def setup_method(self, method):

        # create a dataset for each test
        s = Dataset(**PICS_OF_CATS_DATASET)
        self.dataverse.add_dataset(s)
        self.dataset = self.dataverse.get_dataset_by_doi(s.doi)

    def teardown_method(self, method):
        try:
            self.dataverse.delete_dataset(self.dataset)
        finally:
            return

    def test_create_dataset_from_xml(self):
        new_dataset = Dataset.from_xml_file(ATOM_DATASET)
        self.dataverse.add_dataset(new_dataset)
        retrieved_dataset = self.dataverse.get_dataset_by_title('Roasting at Home')
        assert retrieved_dataset
        self.dataverse.delete_dataset(retrieved_dataset)

    def test_add_files(self):
        self.dataset.add_files(EXAMPLE_FILES)
        actual_files = [f.name for f in self.dataset.get_files()]

        assert '__init__.py' in actual_files
        assert 'config.py' in actual_files

    def test_upload_file(self):
        self.dataset.upload_file('file.txt', 'This is a simple text file!')
        self.dataset.upload_file('file2.txt', 'This is the second simple text file!')
        actual_files = [f.name for f in self.dataset.get_files()]

        assert 'file.txt' in actual_files
        assert 'file2.txt' in actual_files

    def test_display_atom_entry(self):
        # this just tests we can get an entry back, but does
        # not do anything with that xml yet. however, we do use get_entry
        # in other methods so this test case is probably covered
        assert self.dataset.get_entry()
        
    def test_display_dataset_statement(self):
        # this just tests we can get an entry back, but does
        # not do anything with that xml yet. however, we do use get_statement
        # in other methods so this test case is probably covered
        assert self.dataset.get_statement()
    
    def test_delete_a_file(self):
        self.dataset.upload_file('cat.jpg', b'Whatever a cat looks like goes here.')
        
        # Add file and confirm
        files = self.dataset.get_files()
        assert len(files) == 1
        assert files[0].name == 'cat.jpg'
        
        # Delete file and confirm
        self.dataset.delete_file(files[0])
        files = self.dataset.get_files()
        assert not files
        
    def test_delete_a_dataset(self):
        xmlDataset = Dataset.from_xml_file(ATOM_DATASET)
        self.dataverse.add_dataset(xmlDataset)
        atomDataset = self.dataverse.get_dataset_by_title('Roasting at Home')
        num_datasets = len(self.dataverse.get_datasets())

        assert num_datasets > 0
        self.dataverse.delete_dataset(atomDataset)
        assert atomDataset.get_state(refresh=True) == 'DEACCESSIONED'
        assert len(self.dataverse.get_datasets()) == num_datasets - 1

    @pytest.mark.skipif(True, reason='Published datasets can no longer be deaccessioned via API')
    def test_publish_dataset(self):
        assert self.dataset.get_state() == 'DRAFT'
        self.dataset.publish()
        assert self.dataset.get_state() == 'PUBLISHED'
        self.dataverse.delete_dataset(self.dataset)
        assert self.dataset.get_state(refresh=True) == 'DEACCESSIONED'

    
if __name__ == '__main__':
    pytest.main()

