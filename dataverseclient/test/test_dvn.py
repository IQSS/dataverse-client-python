import sys
from time import sleep
import unittest

import logging
logging.basicConfig(level=logging.ERROR)

import sword2

# local modules
from dataverseclient.study import Study
from dataverseclient.connection import DvnConnection
from dataverseclient.example.config import DEFAULT_USERNAME, DEFAULT_HOST, DEFAULT_PASSWORD
from dataverseclient.test.config import PICS_OF_CATS_STUDY, ATOM_STUDY
from dataverseclient import utils


class TestUtils(unittest.TestCase):

    def test_get_element(self):
        with open(ATOM_STUDY) as f:
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
        with open(ATOM_STUDY) as f:
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
        term = 'title'
        formatted_term = utils.format_term(term)
        self.assertEqual(formatted_term, 'dcterms_title')

    def test_format_term_replace(self):
        # A term in the replacement dict
        term = 'id'
        formatted_term = utils.format_term(term)
        self.assertEqual(formatted_term, 'dcterms_identifier')


class TestStudy(unittest.TestCase):

    def test_init(self):
        study = Study(title='My Study', publisher='Mr. Pub Lisher')
        title = utils.get_element(
            study.entry,
            namespace='dcterms',
            tag='title'
        ).text
        publisher = utils.get_element(
            study.entry,
            namespace='dcterms',
            tag='publisher'
        ).text
        self.assertEqual(title, 'My Study')
        self.assertEqual(publisher, 'Mr. Pub Lisher')


class TestStudyOperations(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        
        print "Connecting to DVN."
        self.dvc = DvnConnection(
            username=DEFAULT_USERNAME,
            password=DEFAULT_PASSWORD,
            host=DEFAULT_HOST,
            disable_ssl=True
        )
                        
        print "Getting Dataverse"
        self.dv = self.dvc.get_dataverses()[0]
        self.dv.is_released
        
        print "Removing any existing studies."
        studies = self.dv.get_studies()
        for study in studies :
            if study.get_state() != 'DEACCESSIONED':
                self.dv.delete_study(study)
        
    def setUp(self):
        #runs before each test method
        
        #create a study for each test
        s = Study(**PICS_OF_CATS_STUDY)
        self.dv.add_study(s)
        doi = s.doi
        self.s = self.dv.get_study_by_doi(doi)
        self.assertEqual(doi, self.s.doi)
        return
    
    def tearDown(self):
        try:
            self.dv.delete_study(self.s)
        finally:
            return
    
    def test_create_study_from_xml(self):
        new_study = Study.from_xml_file(ATOM_STUDY)
        self.dv.add_study(new_study)
        retrieved_study = self.dv.get_study_by_title("Roasting at Home")
        self.assertTrue(retrieved_study)
        self.dv.delete_study(retrieved_study)

    def test_add_files(self):
        self.s.add_files(['test_dvn.py', 'config.py'])
        sleep(3) #wait for ingest
        actual_files = [f.name for f in self.s.get_files()]

        self.assertIn('test_dvn.py', actual_files)
        self.assertIn('config.py', actual_files)

    def test_upload_file(self):
        self.s.upload_file('file.txt', 'This is a simple text file!')
        self.s.upload_file('file2.txt', 'This is the second simple text file!')
        sleep(3) #wait for ingest
        actual_files = [f.name for f in self.s.get_files()]
        
        self.assertIn('file.txt', actual_files)
        self.assertIn('file2.txt', actual_files)
        
    def test_display_atom_entry(self):
        # this just tests we can get an entry back, but does
        # not do anything with that xml yet. however, we do use get_entry
        # in other methods so this test case is probably covered
        self.assertTrue(self.s.get_entry())
        
    def test_display_study_statement(self):
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
        
    def test_delete_a_study(self):
        xmlStudy = Study.from_xml_file(ATOM_STUDY)
        self.dv.add_study(xmlStudy)
        atomStudy = self.dv.get_study_by_title("Roasting at Home")
        self.assertTrue(atomStudy)

        startingNumberOfStudies = len(self.dv.get_studies())
        self.assertTrue(startingNumberOfStudies > 0)
        self.dv.delete_study(atomStudy)
        self.assertEqual(len(self.dv.get_studies()), startingNumberOfStudies - 1)
        
    def test_release_study(self):
        self.assertTrue(self.s.get_state() == "DRAFT")
        self.s.release()
        self.assertTrue(self.s.get_state() == "RELEASED")
        self.dv.delete_study(self.s) #this should deaccession
        self.assertTrue(self.s.get_state() == "DEACCESSIONED")
    
    def test_dataverse_released(self):
        self.assertTrue(self.dv.is_released)
    
if __name__ == "__main__":
    __file__ = sys.argv[0]
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStudyOperations)
    unittest.TextTestRunner(verbosity=2).run(suite)

