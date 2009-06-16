import os
import unittest

try:
  from xml.etree import ElementTree
except ImportError, e:
  from elementtree import ElementTree

from htsworkflow.util.ethelp import indent, flatten

class testETHelper(unittest.TestCase):
    def setUp(self):
        self.foo = '<foo><bar>asdf</bar><br/></foo>'
        self.foo_tree = ElementTree.fromstring(self.foo)

    def test_indent(self):
        flat_foo = ElementTree.tostring(self.foo_tree)
        self.failUnlessEqual(len(flat_foo.split('\n')), 1)

        indent(self.foo_tree)
        pretty_foo = ElementTree.tostring(self.foo_tree)
        self.failUnlessEqual(len(pretty_foo.split('\n')), 5)

    def test_flatten(self):
        self.failUnless(flatten(self.foo_tree), 'asdf')

def suite():
    return unittest.makeSuite(testETHelper, 'test')

if __name__ == "__main__":
    unittest.main(defaultTest='suite')




