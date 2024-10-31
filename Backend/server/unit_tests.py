# Unit testing
# by Harris C. McRae
#
# A collection of unit tests for various functions.

import unittest
import src.job_subsystem as js
import src.file_management as fm
from time import sleep
from flask import request
import shutil
import os.path

class Test_File_Management(unittest.TestCase):
    """Tests the file management system"""

    def setUp(self):
        fm.initialise(path='_TESTFILES/')
        fm.clear_folder()
                      
    def test_create_json_file(self):
        status,file,path = fm.create_json_file('TestFile.md')
        self.assertEqual(status, fm.FileStatus.OKAY)
        self.assertEqual(path, '_TESTFILES/TestFile.md')
        self.assertEqual(os.path.isfile('_TESTFILES/TestFile.md'), True)
        file.close()

    def test_duplicate_file(self):
        status,file,path = fm.create_json_file('TestFile.md')
        self.assertEqual(status, fm.FileStatus.OKAY)
        file.close()
        
        status,file,path = fm.create_json_file('TestFile.md')
        self.assertEqual(status, fm.FileStatus.ALREADY_EXIST)

    def test_rename_duplicate(self):
        status,file,path = fm.create_json_file('TestFile.md')
        self.assertEqual(status, fm.FileStatus.OKAY)
        file.close()

        status,file,path2 = fm.create_json_file('TestFile.md', rename=True)
        self.assertEqual(status, fm.FileStatus.OKAY)
        self.assertNotEqual(path, path2)
        file.close()
        

class Test_Job_Subsystem(unittest.TestCase):
    """Tests the job subsystem."""

    def tearDown(self):
        js.debug_wipe_queue()
        js.debug_destroy_waiting()
        js.shutdown(False)
    
    def test_init_1(self):
        self.assertEqual(js.initialise(0.1, 1), js.SubsystemStatus.OKAY)

    def test_init_2(self):
        self.assertEqual(js.initialise(-1, -1), js.SubsystemStatus.INVALID_INPUT)

    def test_running(self):
        js.initialise(0, 1)
        self.assertEqual(js._threadObj.is_alive(), True)
        
    def test_no_job_status(self):
        js.initialise(0.1, 1)
        self.assertEqual( \
            js.check_subsystem_status(), \
            js.SubsystemStatus.NO_JOBS )

    def test_add_job_1(self):
        js.initialise(0.25, 1)
        ret,jID = js.submit_new_job(0)
        self.assertEqual(len(js._jobQueue), 1)

    def test_add_job_2(self):
        js.initialise(3, 1)
        js.submit_new_job(0)
        js.submit_new_job(0)
        self.assertEqual(len(js._jobQueue), 2)

    def test_shutdown_1(self):
        js.initialise(0.1, 1)
        self.assertEqual( \
            js.shutdown(), \
            js.SubsystemStatus.SHUTDOWN )

    def test_shutdown_2(self):
        js.initialise(0.1, 1)
        js.shutdown()
        self.assertEqual(js._threadObj, None)

    def test_shutdown_restart_1(self):
        js.initialise(1, 1)
        js.debug_wipe_queue()
        sleep(0.1)
        for i in range(0, 4):
            js.submit_new_job(i)
        self.assertEqual(len(js._jobQueue), 4)       # 4 jobs submitted
        js.debug_destroy_waiting()
        js.shutdown(True)
        self.assertEqual(js._jobQueue, None)         # Shutdown occurred properly
        js.initialise(1, 1, True)
        self.assertEqual(len(js._jobQueue), 4)       # should still have 4 jobs
        self.assertEqual(js._globalJobCounter, 4)    # should keep the ID at 4

if __name__== '__main__':
    if os.path.isdir('_TESTFILES/'):
        shutil.rmtree('_TESTFILES/')
    unittest.main(verbosity=2)
