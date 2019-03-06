import unittest

from seersync import rsync


class TestRsync(unittest.TestCase):

    def test_indexOfRsync(self):
        self.assertEqual(0, rsync.indexOfRsync(['rsync', 'rsync', 'tail']))
        self.assertEqual(1, rsync.indexOfRsync(['head', 'rsync', 'tail']))
        self.assertEqual(2, rsync.indexOfRsync(['head', 'middle', 'rsync']))
        self.assertGreater(0, rsync.indexOfRsync(['head', 'middle', 'tail']))
        self.assertGreater(0, rsync.indexOfRsync([]))
        self.assertEqual(1, rsync.indexOfRsync(['head', '/usr/bin/rsync', 'tail']))
        self.assertEqual(1, rsync.indexOfRsync(['head', '/usr/bin/rsync', 'rsync']))
        self.assertEqual(2, rsync.indexOfRsync(['head', '/usr/bin/rsync/', 'rsync']))

    def test_makeRsyncCmdLine(self):
        cmdLine = ['rsync', 'tail']
        self.assertEqual(cmdLine, rsync.makeRsyncCmdLine(cmdLine))
        cmdLine = ['/usr/bin/rsync', 'tail']
        self.assertEqual(cmdLine, rsync.makeRsyncCmdLine(cmdLine))
        cmdLine = ['head', 'rsync']
        self.assertEqual(['rsync'] + cmdLine, rsync.makeRsyncCmdLine(cmdLine))
        cmdLine = ['head', '/usr/bin/rsync']
        self.assertEqual(['rsync'] + cmdLine, rsync.makeRsyncCmdLine(cmdLine))
        cmdLine = []
        self.assertEqual(['rsync'] + cmdLine, rsync.makeRsyncCmdLine(cmdLine))

    def test_hasQuietFlag(self):
        self.assertFalse(rsync.hasQuietFlag([]))
        self.assertFalse(rsync.hasQuietFlag(['rsync']))
        self.assertFalse(rsync.hasQuietFlag(['rsync', '-vr', 'q', 'quiet']))
        self.assertTrue(rsync.hasQuietFlag(['rsync', '-vr', '-q', 'quiet']))
        self.assertTrue(rsync.hasQuietFlag(['rsync', '-vr', 'q', '--quiet']))
        self.assertTrue(rsync.hasQuietFlag(['rsync', '-vqr', 'q', 'quiet']))

    def test_ensureDryRun(self):
        self.assertTrue('-n' in rsync._makeSeeRsyncCmdLine(['rsync'])[1:3])
        self.assertTrue('-n' in rsync._makeSeeRsyncCmdLine(['rsync', '-r', 'a/', 'b/'])[1:3])
        self.assertTrue('-n' in rsync._makeSeeRsyncCmdLine(['rsync', '-r', '-n', 'a/', 'b/'])[1:3])


if __name__ == '__main__':
    unittest.main()
