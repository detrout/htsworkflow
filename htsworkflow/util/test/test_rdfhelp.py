import os
import unittest
import types


from datetime import datetime

from htsworkflow.util.rdfhelp import \
     blankOrUri, \
     dump_model, \
     fromTypedNode, \
     get_model, \
     load_string_into_model, \
     rdfsNS, \
     toTypedNode, \
     simplifyUri, \
     sanitize_literal, \
     xsdNS

try:
    import RDF

    class TestRDFHelp(unittest.TestCase):
        def test_from_none(self):
          self.failUnlessEqual(fromTypedNode(None), None)

        def test_typed_node_boolean(self):
            node = toTypedNode(True)
            self.failUnlessEqual(node.literal_value['string'], u'1')
            self.failUnlessEqual(str(node.literal_value['datatype']),
                                 'http://www.w3.org/2001/XMLSchema#boolean')

        def test_bad_boolean(self):
            node = RDF.Node(literal='bad', datatype=xsdNS['boolean'].uri)
            self.failUnlessRaises(ValueError, fromTypedNode, node)

        def test_typed_node_string(self):
            node = toTypedNode('hello')
            self.failUnlessEqual(node.literal_value['string'], u'hello')
            self.failUnless(node.literal_value['datatype'] is None)

        def test_typed_real_like(self):
            num = 3.14
            node = toTypedNode(num)
            self.failUnlessEqual(fromTypedNode(node), num)

        def test_typed_integer(self):
            num = 3
            node = toTypedNode(num)
            self.failUnlessEqual(fromTypedNode(node), num)
            self.failUnlessEqual(type(fromTypedNode(node)), type(num))

        def test_typed_node_string(self):
            s = "Argh matey"
            node = toTypedNode(s)
            self.failUnlessEqual(fromTypedNode(node), s)
            self.failUnlessEqual(type(fromTypedNode(node)), types.UnicodeType)

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

        def test_simplify_uri(self):
            nsOrg = RDF.NS('example.org/example#')
            nsCom = RDF.NS('example.com/example#')

            term = 'foo'
            node = nsOrg[term]
            self.failUnlessEqual(simplifyUri(nsOrg, node), term)
            self.failUnlessEqual(simplifyUri(nsCom, node), None)
            self.failUnlessEqual(simplifyUri(nsOrg, node.uri), term)

        def test_simplify_uri_exceptions(self):
            nsOrg = RDF.NS('example.org/example#')
            nsCom = RDF.NS('example.com/example#')

            node = toTypedNode('bad')
            self.failUnlessRaises(ValueError, simplifyUri, nsOrg, node)
            self.failUnlessRaises(ValueError, simplifyUri, nsOrg, nsOrg)

        def test_owl_import(self):
            path, name = os.path.split(__file__)
            loc = 'file://'+os.path.abspath(path)+'/'
            model = get_model()
            fragment = '''
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

_:a owl:imports "{loc}extra.turtle" .
'''.format(loc=loc)
            load_string_into_model(model, 'turtle', fragment, loc)
            tc = RDF.Node(RDF.Uri('http://jumpgate.caltech.edu/wiki/TestCase'))
            query = RDF.Statement(tc, rdfsNS['label'], None)
            result = list(model.find_statements(query))
            self.failUnlessEqual(len(result), 1)
            self.failUnlessEqual(str(result[0].object), 'TestCase')

        def test_sanitize_literal_text(self):
            self.failUnlessRaises(ValueError, sanitize_literal, "hi")
            hello_text = "hello"
            hello_none = RDF.Node(hello_text)
            self.failUnlessEqual(str(sanitize_literal(hello_none)),
                                 hello_text)
            hello_str = RDF.Node(literal=hello_text,
                                 datatype=xsdNS['string'].uri)
            hello_clean = sanitize_literal(hello_str)
            self.failUnlessEqual(hello_clean.literal_value['string'],
                                 hello_text)

        def test_sanitize_literal_empty_string(self):
            value = ""
            value_node = RDF.Node(value)
            self.assertEqual(str(sanitize_literal(value_node)), value)

        def test_sanitize_literal_html(self):
            hello = "hello <a onload='javascript:alert(\"foo\");' href='http://google.com'>google.com</a>, whats up?"
            hello_clean = 'hello <a href="http://google.com">google.com</a>, whats up?'
            hello_node = RDF.Node(literal=hello,
                                  datatype=xsdNS['string'].uri)
            hello_sanitized = sanitize_literal(hello_node)
            self.failUnlessEqual(hello_sanitized.literal_value['string'],
                                 hello_clean)

            hostile = "hi <b>there</b><script type='text/javascript>alert('boo');</script><a href='javascript:alert('poke')>evil</a> scammer"
            hostile_node = RDF.Node(hostile)
            hostile_sanitized = sanitize_literal(hostile_node)
            # so it drops the stuff after the javascript link.
            # I suppose it could be worse
            hostile_result = """hi <b>there</b>"""
            self.failUnlessEqual(str(hostile_sanitized), hostile_result)


    def suite():
        return unittest.makeSuite(TestRDFHelp, 'test')
except ImportError, e:
    print "Unable to test rdfhelp"

    def suite():
        return None

if __name__ == "__main__":
    unittest.main(defaultTest='suite')
