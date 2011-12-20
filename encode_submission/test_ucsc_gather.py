import unittest

import ucsc_gather

class testUCSCGather(unittest.TestCase):
    pass

def suite():
    return unittest.makeSuite(testUCSCGather,"test")

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
