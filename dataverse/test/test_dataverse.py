from __future__ import print_function, absolute_import

import pytest

import uuid
import httpretty
import requests

from dataverse.connection import Connection
from dataverse.dataset import Dataset
from dataverse.settings import TEST_HOST
from dataverse.test.config import PICS_OF_CATS_DATASET, ATOM_DATASET, EXAMPLE_FILES
from dataverse import exceptions
from dataverse import utils

import logging
logging.basicConfig(level=logging.ERROR)


class DataverseServerTestBase(object):
    """Create a temporary user on `TEST_SERVER` for testing purposes.

    This attaches `username`, `password`, and `token` to the class.
    """

    @classmethod
    def setup_class(cls):
        """Create a temporary user"""
        cls.username = str(uuid.uuid1())
        cls.password = 'p4ssw0rd'
        key = 'burrito'  # hardcoded on test servers
        user_url = 'https://{0}/api/builtin-users?key={1}&password={2}'.format(
            TEST_HOST, key, cls.password,
        )
        user_json = {
            'email': '{0}@gmail.com'.format(cls.username),
            'firstName': 'Namey',
            'lastName': 'Namington',
            'userName': cls.username,
        }

        resp = requests.post(user_url, json=user_json)
        cls.token = resp.json()['data']['apiToken']

    @classmethod
    def teardown_class(cls):
        """Delete the temporary user.

        Note that this will fail if the user has any non-deleted content.
        """
        delete_url = 'https://{0}/api/admin/authenticatedUsers/{1}/'.format(
            TEST_HOST, cls.username,
        )
        resp = requests.delete(delete_url)
        assert resp.status_code == 200


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


class TestConnection(DataverseServerTestBase):

    def test_connect(self):
        connection = Connection(TEST_HOST, self.token)

        assert connection.host == TEST_HOST
        assert connection.token == self.token
        assert connection._service_document

    def test_connect_unauthorized(self):
        with pytest.raises(exceptions.UnauthorizedError):
            Connection(TEST_HOST, 'wrong-token')

    @httpretty.activate
    def test_connect_unknown_failure(self):
        httpretty.register_uri(
            httpretty.GET,
            'https://{host}/dvn/api/data-deposit/v1.1/swordv2/service-document'.format(
                host=TEST_HOST
            ),
            status=400,
        )

        with pytest.raises(exceptions.ConnectionError):
            Connection(TEST_HOST, self.token)

    def test_create_dataverse(self):
        connection = Connection(TEST_HOST, self.token)
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
            connection.delete_dataverse(dataverse)

    def test_delete_dataverse(self):
        connection = Connection(TEST_HOST, self.token)
        alias = str(uuid.uuid1())   # must be unique
        dataverse = connection.create_dataverse(
            alias,
            'Test Name',
            'dataverse@example.com',
        )

        connection.delete_dataverse(dataverse)
        dataverse = connection.get_dataverse(alias)

        assert dataverse is None

    def test_get_dataverses(self):
        connection = Connection(TEST_HOST, self.token)
        original_dataverses = connection.get_dataverses()
        assert isinstance(original_dataverses, list)

        alias = str(uuid.uuid1())   # must be unique

        dataverse = connection.create_dataverse(
            alias,
            'Test Name',
            'dataverse@example.com',
        )

        current_dataverses = connection.get_dataverses()
        try:
            assert len(current_dataverses) == len(original_dataverses) + 1
            assert alias in [dv.alias for dv in current_dataverses]
        finally:
            connection.delete_dataverse(dataverse)

        current_dataverses = connection.get_dataverses()
        assert [dv.alias for dv in current_dataverses] == [dv.alias for dv in original_dataverses]

    def test_get_dataverse(self):
        connection = Connection(TEST_HOST, self.token)
        alias = str(uuid.uuid1())   # must be unique
        assert connection.get_dataverse(alias) is None

        dataverse = connection.create_dataverse(
            alias,
            'Test Name',
            'dataverse@example.com',
        )

        try:
            assert dataverse is not None
            assert dataverse.alias == alias
        finally:
            connection.delete_dataverse(dataverse)


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
        assert publisher == 'Creative Commons CC-BY 3.0 (unported) ' \
                            'http://creativecommons.org/licenses/by/3.0/'


class TestDatasetOperations(DataverseServerTestBase):

    @classmethod
    def setup_class(cls):
        super(TestDatasetOperations, cls).setup_class()

        print('Connecting to Dataverse host at {0}'.format(TEST_HOST))
        cls.connection = Connection(TEST_HOST, cls.token)

        print('Creating test Dataverse')
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
        super(TestDatasetOperations, cls).setup_class()

        print('Removing test Dataverse')
        cls.connection.delete_dataverse(cls.dataverse)
        dataverse = cls.connection.get_dataverse(cls.alias, True)
        assert dataverse is None

    def setup_method(self, method):

        # create a dataset for each test
        dataset = Dataset(**PICS_OF_CATS_DATASET)
        self.dataverse._add_dataset(dataset)
        self.dataset = self.dataverse.get_dataset_by_doi(dataset.doi)

    def teardown_method(self, method):
        try:
            self.dataverse.delete_dataset(self.dataset)
        finally:
            return

    def test_create_dataset(self):
        title = str(uuid.uuid1())   # must be unique
        self.dataverse.create_dataset(title, 'Descripty', 'foo@test.com')
        dataset = self.dataverse.get_dataset_by_title(title)
        try:
            assert dataset.title == title
        finally:
            self.dataverse.delete_dataset(dataset)

    def test_add_dataset_from_xml(self):
        new_dataset = Dataset.from_xml_file(ATOM_DATASET)
        self.dataverse._add_dataset(new_dataset)
        retrieved_dataset = self.dataverse.get_dataset_by_title('Roasting at Home')
        assert retrieved_dataset
        self.dataverse.delete_dataset(retrieved_dataset)

    def test_id_property(self):
        alias = str(uuid.uuid1())
        # Creating a dataverse within a dataverse
        self.connection.create_dataverse(
            alias,
            'Sub Dataverse',
            'dataverse@example.com',
            self.alias,
        )
        sub_dataverse = self.connection.get_dataverse(alias, True)
        assert self.dataset.id == self.dataset._id
        self.connection.delete_dataverse(sub_dataverse)

    def test_add_files(self):
        self.dataset.upload_filepaths(EXAMPLE_FILES)
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
        self.dataverse._add_dataset(xmlDataset)
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
