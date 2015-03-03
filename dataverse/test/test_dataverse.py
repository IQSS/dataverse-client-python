import sys
import unittest

import logging
logging.basicConfig(level=logging.ERROR)

# local modules
from dataverse.dataset import Dataset
from dataverse.connection import Connection
from dataverse.settings import DEFAULT_TOKEN, DEFAULT_HOST
from dataverse.test.config import PICS_OF_CATS_DATASET, ATOM_DATASET
from dataverse import utils


class TestUtils(unittest.TestCase):

    def test_get_element(self):
        with open(ATOM_DATASET) as f:
            entry = f.read()
        # One value
        title = utils.get_element(entry, 'title', 'dcterms').text
        self.assertEqual(title, 'Roasting at Home')
        # Two values
        creator = utils.get_element(entry, 'creator', 'dcterms').text
        self.assertEqual(creator, 'Peets, John')
        # No values
        nonsense = utils.get_element(entry, 'nonsense', 'booga')
        self.assertIsNone(nonsense)

    def test_get_elements(self):
        with open(ATOM_DATASET) as f:
            entry = f.read()
        # One value
        titles = utils.get_elements(entry, 'title', 'dcterms')
        self.assertEqual(len(titles), 1)
        self.assertEqual(titles[0].text, 'Roasting at Home')
        # Two values
        creators = utils.get_elements(entry, 'creator', 'dcterms')
        self.assertEqual(len(creators), 2)
        self.assertEqual(creators[0].text, 'Peets, John')
        self.assertEqual(creators[1].text, 'Stumptown, Jane')
        # No values
        nonsense = utils.get_elements(entry, 'nonsense', 'booga')
        self.assertEqual(nonsense, [])

    def test_format_term(self):
        # A term not in the replacement dict
        formatted_term = utils.format_term('title', namespace='dcterms')
        self.assertEqual(formatted_term, '{http://purl.org/dc/terms/}title')

    def test_format_term_replace(self):
        # A term in the replacement dict
        formatted_term = utils.format_term('id', namespace='dcterms')
        self.assertEqual(formatted_term, '{http://purl.org/dc/terms/}identifier')


class TestDataset(unittest.TestCase):

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
        self.assertEqual(title, 'My Dataset')
        self.assertEqual(title, dataset.title)
        self.assertEqual(publisher, 'Mr. Pub Lisher')

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
        self.assertEqual(title, 'Roasting at Home')
        self.assertEqual(publisher, 'Creative Commons CC-BY 3.0 (unported) http://creativecommons.org/licenses/by/3.0/')


class TestDatasetOperations(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        print "Connecting to DVN."
        self.dvc = Connection(DEFAULT_HOST, DEFAULT_TOKEN)

        print "Getting Dataverse"
        dataverses = self.dvc.get_dataverses()
        if not dataverses:
            raise utils.DataverseException(
                'You must have a published Dataverse to run these tests.'
            )

        self.dv = dataverses[0]
        if not self.dv.is_published:
            raise utils.DataverseException(
                'You must publish "{0}" to run these tests.'.format(self.dv.title)
            )

        print "Removing any existing studies."
        studies = self.dv.get_studies()
        for dataset in studies :
            if dataset.get_state() != 'DEACCESSIONED':
                self.dv.delete_dataset(dataset)
        print 'Dataverse emptied.'

    def setUp(self):
        # runs before each test method

        # create a dataset for each test
        s = Dataset(**PICS_OF_CATS_DATASET)
        self.dv.add_dataset(s)
        doi = s.doi
        self.s = self.dv.get_dataset_by_doi(doi)
        self.assertEqual(doi, self.s.doi)
        return

    def tearDown(self):
        try:
            self.dv.delete_dataset(self.s)
        finally:
            return

    def test_create_dataset_from_xml(self):
        new_dataset = Dataset.from_xml_file(ATOM_DATASET)
        self.dv.add_dataset(new_dataset)
        retrieved_dataset = self.dv.get_dataset_by_title("Roasting at Home")
        self.assertTrue(retrieved_dataset)
        self.dv.delete_dataset(retrieved_dataset)

    def test_add_files(self):
        self.s.add_files(['test_dataverse.py', 'config.py'])
        actual_files = [f.name for f in self.s.get_files()]

        self.assertIn('test_dataverse.py', actual_files)
        self.assertIn('config.py', actual_files)

    def test_upload_file(self):
        self.s.upload_file('file.txt', 'This is a simple text file!')
        self.s.upload_file('file2.txt', 'This is the second simple text file!')
        actual_files = [f.name for f in self.s.get_files()]

        self.assertIn('file.txt', actual_files)
        self.assertIn('file2.txt', actual_files)

    def test_display_atom_entry(self):
        # this just tests we can get an entry back, but does
        # not do anything with that xml yet. however, we do use get_entry
        # in other methods so this test case is probably covered
        self.assertTrue(self.s.get_entry())
        
    def test_display_dataset_statement(self):
        # this just tests we can get an entry back, but does
        # not do anything with that xml yet. however, we do use get_statement
        # in other methods so this test case is probably covered
        self.assertTrue(self.s.get_statement())
    
    def test_delete_a_file(self):
        self.s.upload_file('cat.jpg', b'Whatever a cat looks like goes here.')
        
        #add file and confirm
        files = self.s.get_files()
        cat_file = [f for f in files if f.name == 'cat.jpg']
        self.assertTrue(len(cat_file) == 1)
        
        #delete file and confirm
        self.s.delete_file(cat_file[0])
        files = self.s.get_files()
        cat_file = [f for f in files if f.name == "cat.jpg"]
        self.assertTrue(len(cat_file) == 0)
        
    def test_delete_a_dataset(self):
        xmlDataset = Dataset.from_xml_file(ATOM_DATASET)
        self.dv.add_dataset(xmlDataset)
        atomDataset = self.dv.get_dataset_by_title("Roasting at Home")
        self.assertTrue(atomDataset)

        startingNumberOfStudies = len(self.dv.get_studies())
        self.assertTrue(startingNumberOfStudies > 0)
        self.dv.delete_dataset(atomDataset)
        self.assertEqual(atomDataset.get_state(refresh=True), 'DEACCESSIONED')
        self.assertEqual(len(self.dv.get_studies()), startingNumberOfStudies - 1)

    @unittest.skip('Published studies can no longer be deaccessioned via API')
    def test_publish_dataset(self):
        self.assertTrue(self.s.get_state() == "DRAFT")
        self.s.publish()
        self.assertTrue(self.s.get_state() == "PUBLISHED")
        self.dv.delete_dataset(self.s)
        self.assertTrue(self.s.get_state(refresh=True) == "DEACCESSIONED")
    
    def test_dataverse_published(self):
        self.assertTrue(self.dv.is_published)
    
if __name__ == "__main__":
    __file__ = sys.argv[0]
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDatasetOperations)
    unittest.TextTestRunner(verbosity=2).run(suite)

