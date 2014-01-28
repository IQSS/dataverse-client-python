# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="peterbull"
__date__ ="$Aug 21, 2013 2:56:25 PM$"

import os
import sys
from time import sleep
import unittest
import zipfile

import logging
logging.basicConfig(level=logging.ERROR)

#local modules
import config
import tests as testdata
from study import Study
from connection import DvnConnection


class TestStudyOperations(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        print "Verifying test data."
        assert zipfile.is_zipfile(testdata.INGEST_FILES), 'Invalid tests configuration. %s is not a zipfile' % testdata.INGEST_FILES
        assert os.path.isfile(testdata.PIC_OF_CAT), 'Invalid tests configuration. %s is not a file' % testdata.PIC_OF_CAT
        assert os.path.isfile(testdata.ATOM_STUDY), 'Invalid tests configuration. %s is not a file' % testdata.ATOM_STUDY

        print "Connecting to DVN."
        self.dvc = DvnConnection(username=config.DEFAULT_USERNAME,
                        password=config.DEFAULT_PASSWORD, 
                        host=config.DEFAULT_HOST, 
                        cert=config.DEFAULT_CERT)

        print "Getting Dataverse"
        self.dv = self.dvc.get_dataverses()[0]

    def setUp(self):
        #create a study for each test
        s = Study.CreateStudyFromDict(testdata.PICS_OF_CATS_STUDY)
        self.dv.add_study(s)
        id = s.get_id()
        self.s = self.dv.get_study_by_hdl(id)
        self.assertEqual(id, self.s.get_id())
        return
    
    def tearDown(self):
        try:
            self.dv.delete_study(self.s)
        finally:
            return
    
    def test_create_study_from_xml(self):
        xmlStudy = Study.CreateStudyFromAtomEntryXmlFile(testdata.ATOM_STUDY)
        self.dv.add_study(xmlStudy)
        atomStudy = self.dv.get_study_by_string_in_entry("The first study for the New England Journal of Coffee dataverse")
        self.assertTrue(atomStudy)
        self.dv.delete_study(atomStudy)
        
    def test_add_files_to_study(self):
        zipped_file = zipfile.ZipFile(testdata.INGEST_FILES, 'r')
        expected_files = [os.path.basename(f) for f in zipped_file.namelist()]
        self.s.add_files([testdata.INGEST_FILES])
        sleep(3) #wait for ingest
        actual_files = [f.name for f in self.s.get_files()]
        print 'actual', actual_files
        print 'expected', expected_files
        
        expected_files.sort()
        actual_files.sort()
        
        self.assertEqual(expected_files, actual_files)
        
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
        self.s.add_file(testdata.PIC_OF_CAT)
        test_file = os.path.basename(testdata.PIC_OF_CAT)
        
        #add file and confirm
        files = self.s.get_files()
        catFile = [f for f in files if f.name == test_file]
        self.assertTrue(len(catFile) == 1)
        
        #delete file and confirm
        self.s.delete_file(catFile[0])
        files = self.s.get_files()
        catFile = [f for f in files if f.name == test_file]
        self.assertTrue(len(catFile) == 0)

    def test_delete_a_study(self):
        xmlStudy = Study.CreateStudyFromAtomEntryXmlFile(testdata.ATOM_STUDY)
        self.dv.add_study(xmlStudy)
        atomStudy = self.dv.get_study_by_string_in_entry("The first study for the New England Journal of Coffee dataverse")
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
        self.assertTrue(self.dv.is_released())


if __name__ == "__main__":
    __file__ = sys.argv[0]
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStudyOperations)
    unittest.TextTestRunner(verbosity=2).run(suite)
