import sys
from time import sleep
import unittest

import logging
logging.basicConfig(level=logging.ERROR)

# local modules
from dataverseclient.study import Study
from dataverseclient.connection import DvnConnection
from dataverseclient.example.config import DEFAULT_USERNAME, DEFAULT_HOST, DEFAULT_PASSWORD
from dataverseclient.test.config import PICS_OF_CATS_STUDY, ATOM_STUDY


class TestStudyOperations(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        
        print "Connecting to DVN."
        self.dvc = DvnConnection(username=DEFAULT_USERNAME,
                        password=DEFAULT_PASSWORD,
                        host=DEFAULT_HOST, 
                        disable_ssl_certificate_validation=True)
                        
        print "Getting Dataverse"
        self.dv = self.dvc.get_dataverses()[0]
        
        print "Removing any existing studies."
        studies = self.dv.get_studies()
        for study in studies :
            if study.get_state() != 'DEACCESSIONED':
                self.dv.delete_study(study)
        
    def setUp(self):
        #runs before each test method
        
        #create a study for each test
        s = Study(PICS_OF_CATS_STUDY)
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
        xmlStudy = Study(ATOM_STUDY)
        self.dv.add_study(xmlStudy)
        atomStudy = self.dv.get_study_by_title("Roasting at Home")
        self.assertTrue(atomStudy)
        self.dv.delete_study(atomStudy)
        
    def test_add_file_obj(self):
        self.s.add_file_obj('file.txt', 'This is a simple text file!')
        self.s.add_file_obj('file2.txt', 'This is the second simple text file!')
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
        self.s.add_file_obj('cat.jpg', b'Whatever a cat looks like goes here.')
        
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
        xmlStudy = Study(ATOM_STUDY)
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

