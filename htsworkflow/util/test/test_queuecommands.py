import os
import logging
import time
from unittest import TestCase

from htsworkflow.util.queuecommands import QueueCommands

class testQueueCommands(TestCase):
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

        q = QueueCommands(cmds, 3)
        start = time.time()
        q.run()
        end = time.time()-start
        # we should only take the length of the longest sleep
        self.assertTrue( end > 1.8 and end < 2.2,
                         "took %s seconds, exected ~2" % (end,))

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
        self.assertTrue( end > 3.7 and end < 4.3,
                         "took %s seconds, expected ~4" % (end,))


def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(testQueueCommands))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
