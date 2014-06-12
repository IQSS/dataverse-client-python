# DVN client for SWORD API
# Prereqs: Python, sword2 Module (available using easy_install)
# Adapted from: https://bitbucket.org/beno/python-sword2/wiki/Quickstart
# 

__author__="peterbull"
__date__ ="$Jul 29, 2013 1:38:57 PM$"

# enable logging for sword commands
import logging
logging.basicConfig(level=logging.ERROR)

# python base lib modules
import json
from time import sleep
import traceback

# downloaded modules

# local modules
from dataverseclient.study import Study
from dataverseclient.connection import DvnConnection
from config import DEFAULT_PASSWORD, DEFAULT_HOST, DEFAULT_CERT, DEFAULT_USERNAME, \
    EXAMPLE_DICT


def main():
    
    dv = None # declare outside so except clause has access
    try:
        dvc = DvnConnection(username=DEFAULT_USERNAME,
                        password=DEFAULT_PASSWORD,
                        host=DEFAULT_HOST, 
                        disable_ssl_certificate_validation=True)
                        
        
        dvs = dvc.get_dataverses()
        for dv in dvs:
            print dv
            
        
        dv = dvs[0]
      
        # clean up the test dataverse
        # for study in dv.get_studies():
        #     dv.delete_study(study)
        # print "RELEASED:", dv.is_released()

        s = dv.get_studies()[0]
        # s = Study(EXAMPLE_DICT)
        # s = Study(EXAMPLE_FILE)

        # print s
        print s.get_id()

        # s.delete_all_files()
        # s.add_file("dataverseclient/resources/test/one.txt")
        # s.delete_file(s.get_file("one.txt"))

        # s.add_file("dataverseclient/resources/test")

        s.get_statement()
        print s.get_entry()

        # s.add_files([INGEST_FILES])
        # print s.get_citation()
        # print s.get_state()

        # sleep(3) #wait for ingest`
        
        # fs = s.get_files()
        # print "FILES: ", len(fs)
        # s.delete_file(fs[-1])
        # fs = s.get_files()
        # print "FILES: ", len(fs)
        # s.delete_all_files()
        # fs = s.get_files()
        # print "FILES: ", len(fs)
        
        # s.release()

        # s.hostDataverse.delete_study(s)

        print "\n\nclient succeeded"
        
    except Exception as e:
        sleep(1)
        traceback.print_exc()
        sleep(1)
        if dv:
            try:
                dv.swordConnection.history = json.dumps(dv.connection.swordConnection.history, indent=True)
            except:
                pass
            #print "Call History:\n", dv.connection.swordConnection.history

if __name__ == "__main__":
    main()
