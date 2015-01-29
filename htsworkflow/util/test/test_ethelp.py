import os
from unittest import TestCase

try:
  from xml.etree import ElementTree
except ImportError as e:
  from elementtree import ElementTree

from htsworkflow.util.ethelp import indent, flatten

class testETHelper(TestCase):
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
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(testETHelper))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
