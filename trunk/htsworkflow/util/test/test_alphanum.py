import copy
import os
import unittest

from htsworkflow.util.alphanum import alphanum

class testAlphanum(unittest.TestCase):
    def test_string(self):
      unsorted = ['z5', 'b3', 'b10', 'a001', 'a2']
      sorted = [ 'a001', 'a2', 'b3', 'b10', 'z5']
      scratch = copy.copy(unsorted)
      scratch.sort(alphanum)

      for i in xrange(len(scratch)):
        self.failIfEqual(scratch[i], unsorted[i])
      for i in xrange(len(scratch)):
        self.failUnlessEqual(scratch[i], sorted[i])

    def test_numbers(self):
      unsorted = [5,7,10,18,-1,3]
      sorted = [-1,3,5,7,10,18]
      scratch = copy.copy(unsorted)
      scratch.sort(alphanum)

      for i in xrange(len(scratch)):
        self.failIfEqual(scratch[i], unsorted[i])
      for i in xrange(len(scratch)):
        self.failUnlessEqual(scratch[i], sorted[i])


def suite():
    return unittest.makeSuite(testAlphanum, 'test')

if __name__ == "__main__":
    unittest.main(defaultTest='suite')




