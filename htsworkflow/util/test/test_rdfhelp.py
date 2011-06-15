import unittest

from htsworkflow.util.rdfhelp import toTypedNode, blankOrUri

class TestRDFHelp(unittest.TestCase):
    def test_typed_node_boolean(self):
        node = toTypedNode(True)
        self.failUnlessEqual(node.literal_value['string'], u'1')
        self.failUnlessEqual(str(node.literal_value['datatype']),
                             'http://www.w3.org/2001/XMLSchema#boolean')

    def test_typed_node_string(self):
        node = toTypedNode('hello')
        self.failUnlessEqual(node.literal_value['string'], u'hello')
        self.failUnlessEqual(str(node.literal_value['datatype']),
                             'http://www.w3.org/2001/XMLSchema#string')

    def test_blank_or_uri_blank(self):
        node = blankOrUri()
        self.failUnlessEqual(node.is_blank(), True)

    def test_blank_or_uri_url(self):
        s = 'http://google.com'
        node = blankOrUri(s)
        self.failUnlessEqual(node.is_resource(), True)
        self.failUnlessEqual(str(node.uri), s)
        
def suite():
    return unittest.makeSuite(testRdfHelp, 'test')

if __name__ == "__main__":
    unittest.main(defaultTest='suite')
