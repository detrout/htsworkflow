import os
import types
from unittest import TestCase

from datetime import datetime

from htsworkflow.util.rdfhelp import \
     add_default_schemas, \
     blankOrUri, \
     dcNS, \
     dump_model, \
     fromTypedNode, \
     get_model, \
     guess_parser, \
     guess_parser_by_extension, \
     load_string_into_model, \
     owlNS, \
     rdfNS, \
     rdfsNS, \
     remove_schemas, \
     toTypedNode, \
     strip_namespace, \
     simplify_uri, \
     sanitize_literal, \
     xsdNS

try:
    import RDF

    class TestRDFHelp(TestCase):
        def test_from_none(self):
          self.assertEqual(fromTypedNode(None), None)

        def test_typed_node_boolean(self):
            node = toTypedNode(True)
            self.assertIn(node.literal_value['string'], (u'1', u'true'))
            self.assertEqual(str(node.literal_value['datatype']),
                                 'http://www.w3.org/2001/XMLSchema#boolean')

        def test_bad_boolean(self):
            node = RDF.Node(literal='bad', datatype=xsdNS['boolean'].uri)
            # older versions of librdf ~< 1.0.16 left the literal
            # alone. and thus should fail the fromTypedNode call
            # newer versions coerced the odd value to false.
            try:
                self.assertFalse(fromTypedNode(node))
            except ValueError as e:
                pass

        def test_typed_node_string(self):
            node = toTypedNode('hello')
            self.assertEqual(node.literal_value['string'], u'hello')
            self.assertTrue(node.literal_value['datatype'] is None)

        def test_typed_real_like(self):
            num = 3.14
            node = toTypedNode(num)
            self.assertEqual(fromTypedNode(node), num)

        def test_typed_integer(self):
            num = 3
            node = toTypedNode(num)
            self.assertEqual(fromTypedNode(node), num)
            self.assertEqual(type(fromTypedNode(node)), type(num))

        def test_typed_node_string(self):
            s = "Argh matey"
            node = toTypedNode(s)
            self.assertEqual(fromTypedNode(node), s)
            self.assertEqual(type(fromTypedNode(node)), types.UnicodeType)

        def test_blank_or_uri_blank(self):
            node = blankOrUri()
            self.assertEqual(node.is_blank(), True)

        def test_blank_or_uri_url(self):
            s = 'http://google.com'
            node = blankOrUri(s)
            self.assertEqual(node.is_resource(), True)
            self.assertEqual(str(node.uri), s)

        def test_blank_or_uri_node(self):
            s = RDF.Node(RDF.Uri('http://google.com'))
            node = blankOrUri(s)
            self.assertEqual(node.is_resource(), True)
            self.assertEqual(node, s)

        def test_unicode_node_roundtrip(self):
            literal = u'\u5927'
            roundtrip = fromTypedNode(toTypedNode(literal))
            self.assertEqual(roundtrip, literal)
            self.assertEqual(type(roundtrip), types.UnicodeType)

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

        def test_strip_namespace_uri(self):
            nsOrg = RDF.NS('example.org/example#')
            nsCom = RDF.NS('example.com/example#')

            term = 'foo'
            node = nsOrg[term]
            self.assertEqual(strip_namespace(nsOrg, node), term)
            self.assertEqual(strip_namespace(nsCom, node), None)
            self.assertEqual(strip_namespace(nsOrg, node.uri), term)

        def test_strip_namespace_exceptions(self):
            nsOrg = RDF.NS('example.org/example#')
            nsCom = RDF.NS('example.com/example#')

            node = toTypedNode('bad')
            self.assertRaises(ValueError, strip_namespace, nsOrg, node)
            self.assertRaises(ValueError, strip_namespace, nsOrg, nsOrg)

        def test_simplify_uri(self):
            DATA = [('http://asdf.org/foo/bar', 'bar'),
                    ('http://asdf.org/foo/bar#bleem', 'bleem'),
                    ('http://asdf.org/foo/bar/', 'bar'),
                    ('http://asdf.org/foo/bar?was=foo', 'was=foo')]

            for uri, expected in DATA:
                self.assertEqual(simplify_uri(uri), expected)

            for uri, expected in DATA:
                n = RDF.Uri(uri)
                self.assertEqual(simplify_uri(n), expected)

            for uri, expected in DATA:
                n = RDF.Node(RDF.Uri(uri))
                self.assertEqual(simplify_uri(n), expected)

            # decoding literals is questionable
            n = toTypedNode('http://foo/bar')
            self.assertRaises(ValueError, simplify_uri, n)

        def test_owl_import(self):
            path, name = os.path.split(__file__)
            #loc = 'file://'+os.path.abspath(path)+'/'
            loc = os.path.abspath(path)+'/'
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
            self.assertEqual(len(result), 1)
            self.assertEqual(str(result[0].object), 'TestCase')

        def test_sanitize_literal_text(self):
            self.assertRaises(ValueError, sanitize_literal, "hi")
            hello_text = "hello"
            hello_none = RDF.Node(hello_text)
            self.assertEqual(str(sanitize_literal(hello_none)),
                                 hello_text)
            hello_str = RDF.Node(literal=hello_text,
                                 datatype=xsdNS['string'].uri)
            hello_clean = sanitize_literal(hello_str)
            self.assertEqual(hello_clean.literal_value['string'],
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
            self.assertEqual(hello_sanitized.literal_value['string'],
                                 hello_clean)

            hostile = "hi <b>there</b><script type='text/javascript>alert('boo');</script><a href='javascript:alert('poke')>evil</a> scammer"
            hostile_node = RDF.Node(hostile)
            hostile_sanitized = sanitize_literal(hostile_node)
            # so it drops the stuff after the javascript link.
            # I suppose it could be worse
            hostile_result = """hi <b>there</b>"""
            self.assertEqual(str(hostile_sanitized), hostile_result)

        def test_guess_parser_from_file(self):
            DATA = [
                ('/a/b/c.rdf', 'rdfxml'),
                ('/a/b/c.xml', 'rdfxml'),
                ('/a/b/c.html', 'rdfa'),
                ('/a/b/c.turtle', 'turtle'),
                ('http://foo.bar/bleem.turtle', 'turtle')]
            for path, parser in DATA:
                self.assertEqual(guess_parser_by_extension(path), parser)
                self.assertEqual(guess_parser(None, path), parser)

            DATA = [
                ('application/rdf+xml', 'http://a.org/b/c', 'rdfxml'),
                ('application/x-turtle', 'http://a.org/b/c', 'turtle'),
                ('text/html', 'http://a.org/b/c', 'rdfa'),
                ('text/html', 'http://a.org/b/c.html', 'rdfa'),
                ('text/plain', 'http://a.org/b/c.turtle', 'turtle'),
                ('text/plain', 'http://a.org/b/c', 'guess')
            ]
            for contenttype, url, parser in DATA:
                self.assertEqual(guess_parser(contenttype, url), parser)

    class TestRDFSchemas(TestCase):
        def test_rdf_schema(self):
            """Does it basically work?
            """
            model = get_model()
            self.assertEqual(model.size(), 0)
            add_default_schemas(model)
            self.assertTrue(model.size() > 0)
            remove_schemas(model)
            self.assertEqual(model.size(), 0)

        def test_included_schemas(self):
            model = get_model()
            add_default_schemas(model)

            # rdf test
            s = RDF.Statement(rdfNS[''], dcNS['title'], None)
            title = model.get_target(rdfNS[''], dcNS['title'])
            self.assertTrue(title is not None)

            s = RDF.Statement(rdfNS['Property'], rdfNS['type'], rdfsNS['Class'])
            self.assertTrue(model.contains_statement(s))

            # rdfs test
            s = RDF.Statement(rdfsNS['Class'], rdfNS['type'], rdfsNS['Class'])
            self.assertTrue(model.contains_statement(s))

            s = RDF.Statement(owlNS['inverseOf'], rdfNS['type'],
                              rdfNS['Property'])
            self.assertTrue(model.contains_statement(s))


except ImportError as e:
    print "Unable to test rdfhelp"

def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestRDFHelp))
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestRDFSchemas))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
