import os
import logging
import time
import unittest


from gaworkflow.util.queuecommands import QueueCommands

class testQueueCommands(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(name)-8s %(message)s')

       

    def test_unlimited_run_slow(self):
        """
        Run everything at once
        """
        cmds = ['/bin/sleep 0',
                '/bin/sleep 1',
                '/bin/sleep 2',]

        q = QueueCommands(cmds)
        start = time.time()
        q.run()
        end = time.time()-start
        # we should only take the length of the longest sleep
        # pity I had to add a 1 second sleep
        self.failUnless( end > 2.9 and end < 3.1,
                         "took %s seconds, exected ~3" % (end,))

    def test_limited_run_slow(self):
        """
        Run a limited number of jobs
        """
        cmds = ['/bin/sleep 1',
                '/bin/sleep 2',
                '/bin/sleep 3',]

        q = QueueCommands(cmds, 2)

        start = time.time()
        q.run()
        end = time.time()-start
        # pity I had to add a 1 second sleep
        self.failUnless( end > 5.9 and end < 6.1,
                         "took %s seconds, expected ~6" % (end,)) 

def suite():
    return unittest.makeSuite(testQueueCommands, 'test')

if __name__ == "__main__":
    unittest.main(defaultTest='suite')




