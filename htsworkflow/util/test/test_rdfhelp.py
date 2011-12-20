import unittest
import types

from datetime import datetime

from htsworkflow.util.rdfhelp import \
     blankOrUri, \
     toTypedNode, \
     fromTypedNode, \
     xsdNS

try:
  import RDF

  class TestRDFHelp(unittest.TestCase):
      def test_typed_node_boolean(self):
          node = toTypedNode(True)
          self.failUnlessEqual(node.literal_value['string'], u'1')
          self.failUnlessEqual(str(node.literal_value['datatype']),
                               'http://www.w3.org/2001/XMLSchema#boolean')

      def test_typed_node_string(self):
          node = toTypedNode('hello')
          self.failUnlessEqual(node.literal_value['string'], u'hello')
          self.failUnless(node.literal_value['datatype'] is None)

      def test_blank_or_uri_blank(self):
          node = blankOrUri()
          self.failUnlessEqual(node.is_blank(), True)

      def test_blank_or_uri_url(self):
          s = 'http://google.com'
          node = blankOrUri(s)
          self.failUnlessEqual(node.is_resource(), True)
          self.failUnlessEqual(str(node.uri), s)

      def test_blank_or_uri_node(self):
          s = RDF.Node(RDF.Uri('http://google.com'))
          node = blankOrUri(s)
          self.failUnlessEqual(node.is_resource(), True)
          self.failUnlessEqual(node, s)

      def test_unicode_node_roundtrip(self):
          literal = u'\u5927'
          roundtrip = fromTypedNode(toTypedNode(literal))
          self.failUnlessEqual(roundtrip, literal)
          self.failUnlessEqual(type(roundtrip), types.UnicodeType)

      def test_datetime_no_microsecond(self):
          dateTimeType = xsdNS['dateTime'].uri
          short_isostamp = '2011-12-20T11:44:25'
          short_node = RDF.Node(literal=short_isostamp,
                               datatype=dateTimeType)
          short_datetime = datetime(2011,12,20,11,44,25)

          self.assertEqual(fromTypedNode(short_node), short_datetime)
          self.assertEqual(toTypedNode(short_datetime), short_node)
          self.assertEqual(fromTypedNode(toTypedNode(short_datetime)),
                           short_datetime)

      def test_datetime_with_microsecond(self):
          dateTimeType = xsdNS['dateTime'].uri
          long_isostamp = '2011-12-20T11:44:25.081776'
          long_node = RDF.Node(literal=long_isostamp,
                               datatype=dateTimeType)
          long_datetime = datetime(2011,12,20,11,44,25,81776)

          self.assertEqual(fromTypedNode(long_node), long_datetime)
          self.assertEqual(toTypedNode(long_datetime), long_node)
          self.assertEqual(fromTypedNode(toTypedNode(long_datetime)),
                           long_datetime)

  def suite():
      return unittest.makeSuite(testRdfHelp, 'test')
except ImportError, e:
    print "Unable to test rdfhelp"

    def suite():
        return None

if __name__ == "__main__":
    unittest.main(defaultTest='suite')
