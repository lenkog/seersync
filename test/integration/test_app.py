import os
import shutil
import tarfile
import unittest
from unittest.mock import patch, call

from seersync import app
from seersync._version import __version__


class TestApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cwd = os.getcwd()
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        with tarfile.open('data/case1.tar', 'r') as case1:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(case1, path="data")

    @classmethod
    def tearDownClass(cls):
        try:
            shutil.rmtree('data/case1')
        finally:
            os.chdir(cls.cwd)

    @patch('builtins.print')
    def test_simple(self, mockPrint):
        app.main(['-b', 'rsync', '-r', 'data/case1/src/', 'data/case1/dst/'])
        self.assertEqual(6, len(mockPrint.mock_calls))
        self.assertTrue(mockPrint.mock_calls[0][1][0].startswith('rsync command line:'))
        self.assertEqual(call('M', 'modified dir/nested modified file'), mockPrint.mock_calls[1])
        self.assertEqual(call('A', 'modified dir/nested new file'), mockPrint.mock_calls[2])
        self.assertEqual(call('M', 'modified file'), mockPrint.mock_calls[3])
        self.assertEqual(call('A', 'new dir/'), mockPrint.mock_calls[4])
        self.assertEqual(call('A', 'new file'), mockPrint.mock_calls[5])

    @patch('builtins.print')
    def test_mirror(self, mockPrint):
        app.main(['-b', 'rsync', '-a', '--delete', 'data/case1/src/', 'data/case1/dst/'])
        self.assertEqual(14, len(mockPrint.mock_calls))
        self.assertTrue(mockPrint.mock_calls[0][1][0].startswith('rsync command line:'))
        self.assertEqual(call('M', './'), mockPrint.mock_calls[1])
        self.assertEqual(call('M', 'modified dir/'), mockPrint.mock_calls[2])
        self.assertEqual(call('M', 'modified dir/nested modified file'), mockPrint.mock_calls[3])
        self.assertEqual(call('A', 'modified dir/nested new file'), mockPrint.mock_calls[4])
        self.assertEqual(call('D', 'modified dir/nested surplus file'), mockPrint.mock_calls[5])
        self.assertEqual(call('M', 'modified file'), mockPrint.mock_calls[6])
        self.assertEqual(call('M', 'modified link'), mockPrint.mock_calls[7])
        self.assertEqual(call('A', 'new dir/'), mockPrint.mock_calls[8])
        self.assertEqual(call('A', 'new file'), mockPrint.mock_calls[9])
        self.assertEqual(call('A', 'new link'), mockPrint.mock_calls[10])
        self.assertEqual(call('D', 'surplus dir/'), mockPrint.mock_calls[11])
        self.assertEqual(call('D', 'surplus file'), mockPrint.mock_calls[12])
        self.assertEqual(call('D', 'surplus link'), mockPrint.mock_calls[13])

    @patch('builtins.print')
    def test_noNew(self, mockPrint):
        app.main(['-b', 'rsync', '-a', '--existing', '--delete', 'data/case1/src/', 'data/case1/dst/'])
        self.assertEqual(10, len(mockPrint.mock_calls))
        self.assertTrue(mockPrint.mock_calls[0][1][0].startswith('rsync command line:'))
        self.assertEqual(call('M', './'), mockPrint.mock_calls[1])
        self.assertEqual(call('M', 'modified dir/'), mockPrint.mock_calls[2])
        self.assertEqual(call('M', 'modified dir/nested modified file'), mockPrint.mock_calls[3])
        self.assertEqual(call('D', 'modified dir/nested surplus file'), mockPrint.mock_calls[4])
        self.assertEqual(call('M', 'modified file'), mockPrint.mock_calls[5])
        self.assertEqual(call('M', 'modified link'), mockPrint.mock_calls[6])
        self.assertEqual(call('D', 'surplus dir/'), mockPrint.mock_calls[7])
        self.assertEqual(call('D', 'surplus file'), mockPrint.mock_calls[8])
        self.assertEqual(call('D', 'surplus link'), mockPrint.mock_calls[9])

    @patch('builtins.print')
    def test_noUpdates(self, mockPrint):
        app.main(['-b', 'rsync', '-a', '--ignore-existing', '--delete', 'data/case1/src/', 'data/case1/dst/'])
        self.assertEqual(11, len(mockPrint.mock_calls))
        self.assertTrue(mockPrint.mock_calls[0][1][0].startswith('rsync command line:'))
        self.assertEqual(call('M', './'), mockPrint.mock_calls[1])
        self.assertEqual(call('M', 'modified dir/'), mockPrint.mock_calls[2])
        self.assertEqual(call('A', 'modified dir/nested new file'), mockPrint.mock_calls[3])
        self.assertEqual(call('D', 'modified dir/nested surplus file'), mockPrint.mock_calls[4])
        self.assertEqual(call('A', 'new dir/'), mockPrint.mock_calls[5])
        self.assertEqual(call('A', 'new file'), mockPrint.mock_calls[6])
        self.assertEqual(call('A', 'new link'), mockPrint.mock_calls[7])
        self.assertEqual(call('D', 'surplus dir/'), mockPrint.mock_calls[8])
        self.assertEqual(call('D', 'surplus file'), mockPrint.mock_calls[9])
        self.assertEqual(call('D', 'surplus link'), mockPrint.mock_calls[10])

    @patch('builtins.print')
    def test_noDeletes(self, mockPrint):
        app.main(['-b', 'rsync', '-a', 'data/case1/src/', 'data/case1/dst/'])
        self.assertEqual(10, len(mockPrint.mock_calls))
        self.assertTrue(mockPrint.mock_calls[0][1][0].startswith('rsync command line:'))
        self.assertEqual(call('M', './'), mockPrint.mock_calls[1])
        self.assertEqual(call('M', 'modified dir/'), mockPrint.mock_calls[2])
        self.assertEqual(call('M', 'modified dir/nested modified file'), mockPrint.mock_calls[3])
        self.assertEqual(call('A', 'modified dir/nested new file'), mockPrint.mock_calls[4])
        self.assertEqual(call('M', 'modified file'), mockPrint.mock_calls[5])
        self.assertEqual(call('M', 'modified link'), mockPrint.mock_calls[6])
        self.assertEqual(call('A', 'new dir/'), mockPrint.mock_calls[7])
        self.assertEqual(call('A', 'new file'), mockPrint.mock_calls[8])
        self.assertEqual(call('A', 'new link'), mockPrint.mock_calls[9])

    @patch('builtins.print')
    def test_ignoreVerboseOutput(self, mockPrint):
        app.main(['-b', 'rsync', '-vv', '--progress', '-r', 'data/case1/src/', 'data/case1/dst/'])
        self.assertEqual(6, len(mockPrint.mock_calls))
        self.assertTrue(mockPrint.mock_calls[0][1][0].startswith('rsync command line:'))
        self.assertEqual(call('M', 'modified dir/nested modified file'), mockPrint.mock_calls[1])
        self.assertEqual(call('A', 'modified dir/nested new file'), mockPrint.mock_calls[2])
        self.assertEqual(call('M', 'modified file'), mockPrint.mock_calls[3])
        self.assertEqual(call('A', 'new dir/'), mockPrint.mock_calls[4])
        self.assertEqual(call('A', 'new file'), mockPrint.mock_calls[5])

    @patch('builtins.print')
    def test_inputFile(self, mockPrint):
        """
        This test covers a few things:
        - specifying input file overrides the rsync command line provided as arguments
        - passing 'rsync' as the input file name is correctly interpreted
        - comments in the input file are correctly ignored
        """
        app.main(['-b', '-i', 'rsync', 'rsync', '-a', 'data/case1/src/', 'data/case1/dst/'])
        self.assertEqual(6, len(mockPrint.mock_calls))
        self.assertTrue(mockPrint.mock_calls[0][1][0].startswith('rsync command line:'))
        self.assertEqual(call('M', 'modified dir/nested modified file'), mockPrint.mock_calls[1])
        self.assertEqual(call('A', 'modified dir/nested new file'), mockPrint.mock_calls[2])
        self.assertEqual(call('M', 'modified file'), mockPrint.mock_calls[3])
        self.assertEqual(call('A', 'new dir/'), mockPrint.mock_calls[4])
        self.assertEqual(call('A', 'new file'), mockPrint.mock_calls[5])

    @patch('seersync.ui.launch')
    @patch('builtins.print')
    def test_inputFileNotSpecified(self, _, mockLaunch):
        # argparse exists if it can't parse arguments successfully
        with self.assertRaises(SystemExit):
            app.main(['-b', '-i', 'rsync', '-a', 'data/case1/src/', 'data/case1/dst/'])
        with self.assertRaises(SystemExit):
            app.main(['-i', 'rsync', '-a', 'data/case1/src/', 'data/case1/dst/'])
        self.assertEqual(0, len(mockLaunch.mock_calls))

    @patch('seersync.ui.launch')
    @patch('builtins.print')
    def test_missingInputFile(self, mockPrint, mockLaunch):
        with self.assertRaises(SystemExit):
            app.main(['-b', '-i', 'missingFile'])
        self.assertEqual(1, len(mockPrint.mock_calls))
        self.assertTrue(mockPrint.mock_calls[0][1][0].startswith('Error'))
        self.assertTrue('missingFile' in mockPrint.mock_calls[0][1][1])
        with self.assertRaises(SystemExit):
            app.main(['-b', '-i', 'missingFile'])
        self.assertEqual(2, len(mockPrint.mock_calls))
        self.assertTrue(mockPrint.mock_calls[1][1][0].startswith('Error'))
        self.assertTrue('missingFile' in mockPrint.mock_calls[1][1][1])
        self.assertEqual(0, len(mockLaunch.mock_calls))

    @patch('seersync.ui.launch')
    @patch('builtins.print')
    def test_batchMode(self, _, mockLaunch):
        app.main(['-b', 'rsync', 'data/case1/src/', 'data/case1/dst/'])
        self.assertEqual(0, len(mockLaunch.mock_calls))
        app.main(['rsync', 'data/case1/src/', 'data/case1/dst/'])
        self.assertEqual(1, len(mockLaunch.mock_calls))

    @patch('builtins.print')
    def test_progress(self, mockPrint):
        app.main(['-b', '--progress', 'rsync', '-r', 'data/case1/src/', 'data/case1/dst/'])
        self.assertLess(6, len(mockPrint.mock_calls))
        self.assertTrue(mockPrint.mock_calls[0][1][0].startswith('rsync command line:'))
        self.assertTrue('items received' in mockPrint.mock_calls[1][1][0])

    @patch('builtins.print')
    def test_dontParseRsyncArgs(self, mockPrint):
        """
        Here we test that the --progress argument in the rsync command line isn't interpreted as ours
        """
        app.main(['-b', 'rsync', '--progress', '-r', 'data/case1/src/', 'data/case1/dst/'])
        self.assertEqual(6, len(mockPrint.mock_calls))
        self.assertTrue(mockPrint.mock_calls[0][1][0].startswith('rsync command line:'))
        self.assertFalse('items received' in mockPrint.mock_calls[1][1][0])

    @patch('seersync.ui.launch')
    @patch('builtins.print')
    def test_version(self, mockPrint, mockLaunch):
        app.main(['-b', '--version', 'rsync', '-r', 'data/case1/src/', 'data/case1/dst/'])
        self.assertEqual(1, len(mockPrint.mock_calls))
        self.assertEqual('seersync ' + __version__, mockPrint.mock_calls[0][1][0])
        app.main(['--version', 'rsync', '-r', 'data/case1/src/', 'data/case1/dst/'])
        self.assertEqual(2, len(mockPrint.mock_calls))
        self.assertEqual(mockPrint.mock_calls[0], mockPrint.mock_calls[1])
        self.assertEqual(0, len(mockLaunch.mock_calls))

    @patch('builtins.print')
    def test_noItemsWithoutQuiet(self, mockPrint):
        app.main(['-b', 'rsync', '--existing', '--ignore-existing', 'data/case1/src/', 'data/case1/dst/'])
        self.assertEqual(1, len(mockPrint.mock_calls))
        self.assertTrue(mockPrint.mock_calls[0][1][0].startswith('rsync command line:'))

    @patch('builtins.print')
    def test_detectQuiet(self, _):
        with self.assertRaises(SystemExit):
            app.main(['-b', 'rsync', '-r', '-q', 'data/case1/src/', 'data/case1/dst/'])
        with self.assertRaises(SystemExit):
            app.main(['-b', 'rsync', '-r', '--quiet', 'data/case1/src/', 'data/case1/dst/'])
        with self.assertRaises(SystemExit):
            app.main(['-b', 'rsync', '-rqv', 'data/case1/src/', 'data/case1/dst/'])

    @patch('builtins.print')
    def test_skipDetectQuiet(self, _):
        try:
            app.main(['-b', '--skip-detect-quiet', 'rsync', '-r', '-q', 'data/case1/src/', 'data/case1/dst/'])
        except SystemExit:
            self.fail()
        try:
            app.main(['-b', '--skip-detect-quiet', 'rsync', '-r', '--quiet', 'data/case1/src/', 'data/case1/dst/'])
        except SystemExit:
            self.fail()
        try:
            app.main(['-b', '--skip-detect-quiet', 'rsync', '-rqv', 'data/case1/src/', 'data/case1/dst/'])
        except SystemExit:
            self.fail()

    @patch('seersync.ui.launch')
    @patch('builtins.print')
    def test_help(self, _, mockLaunch):
        # argparse exists if one sends the help option
        with self.assertRaises(SystemExit):
            app.main(['-b', '--help', 'rsync', '-r', 'data/case1/src/', 'data/case1/dst/'])
        with self.assertRaises(SystemExit):
            app.main(['-b', '-h', 'rsync', '-r', 'data/case1/src/', 'data/case1/dst/'])
        with self.assertRaises(SystemExit):
            app.main(['-bh', 'rsync', '-r', 'data/case1/src/', 'data/case1/dst/'])
        with self.assertRaises(SystemExit):
            app.main(['--help', 'rsync', '-r', 'data/case1/src/', 'data/case1/dst/'])
        with self.assertRaises(SystemExit):
            app.main(['-h', 'rsync', '-r', 'data/case1/src/', 'data/case1/dst/'])
        self.assertEqual(0, len(mockLaunch.mock_calls))


if __name__ == '__main__':
    unittest.main()
