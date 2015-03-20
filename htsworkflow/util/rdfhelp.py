"""Helper features for working with librdf
"""
from __future__ import print_function

import collections
from datetime import datetime
from glob import glob
import six
from six.moves import urllib
import logging
import os
import sys
import types
from pkg_resources import resource_listdir, resource_string

import lxml.html
import lxml.html.clean
import RDF

logger = logging.getLogger(__name__)

from htsworkflow.util.rdfns import *

SCHEMAS_URL='http://jumpgate.caltech.edu/phony/schemas'
INFERENCE_URL='http://jumpgate.caltech.edu/phony/inference'

ISOFORMAT_MS = "%Y-%m-%dT%H:%M:%S.%f"
ISOFORMAT_SHORT = "%Y-%m-%dT%H:%M:%S"

def sparql_query(model, query_filename, output_format='text'):
    """Execute sparql query from file
    """
    logger.info("Opening: %s" % (query_filename,))
    query_body = open(query_filename, 'r').read()
    query = RDF.SPARQLQuery(query_body)
    results = query.execute(model)
    if output_format == 'html':
        html_query_results(results)
    else:
        display_query_results(results)


def display_query_results(results):
    """A very simple display of sparql query results showing name value pairs
    """
    for row in results:
        for k, v in row.items()[::-1]:
            print("{0}: {1}".format(k, v))
        print()

def html_query_results(result_stream):
    from django.conf import settings
    from django.template import Context, loader

    # I did this because I couldn't figure out how to
    # get simplify_rdf into the django template as a filter
    class Simplified(object):
        def __init__(self, value):
            self.simple = simplify_rdf(value)
            if value.is_resource():
                self.url = value
            else:
                self.url = None

    template = loader.get_template('rdf_report.html')
    results = []
    for row in result_stream:
        new_row = collections.OrderedDict()
        row_urls = []
        for k,v in row.items():
            new_row[k] = Simplified(v)
        results.append(new_row)
    context = Context({'results': results,})
    print(template.render(context))

def blankOrUri(value=None):
    """Return a blank node for None or a resource node for strings.
    """
    node = None
    if value is None:
        node = RDF.Node()
    elif isinstance(value, six.string_types):
        node = RDF.Node(uri_string=value)
    elif isinstance(value, RDF.Node):
        node = value

    return node


def toTypedNode(value, language="en"):
    """Convert a python variable to a RDF Node with its closest xsd type
    """
    if isinstance(value, bool):
        value_type = xsdNS['boolean'].uri
        if value:
            value = u'1'
        else:
            value = u'0'
    elif isinstance(value, int):
        value_type = xsdNS['decimal'].uri
        value = str(value)
    elif isinstance(value, float):
        value_type = xsdNS['float'].uri
        value = str(value)
    elif isinstance(value, datetime):
        value_type = xsdNS['dateTime'].uri
        if value.microsecond == 0:
            value = value.strftime(ISOFORMAT_SHORT)
        else:
            value = value.strftime(ISOFORMAT_MS)
    else:
        value_type = None
        if six.PY3:
            value = str(value)
        else:
            value = unicode(value).encode('utf-8')

    if value_type is not None:
        node = RDF.Node(literal=value, datatype=value_type)
    else:
        node = RDF.Node(literal=value, language=language)
    return node


def fromTypedNode(node):
    """Convert a typed RDF Node to its closest python equivalent
    """
    if not isinstance(node, RDF.Node):
        return node
    if node.is_resource():
        return node

    value_type = get_node_type(node)
    literal = node.literal_value['string']
    literal_lower = literal.lower()

    if value_type == 'boolean':
        if literal_lower in ('1', 'yes', 'true'):
            return True
        elif literal_lower in ('0', 'no', 'false'):
            return False
        else:
            raise ValueError("Unrecognized boolean %s" % (literal,))
    elif value_type == 'integer':
        return int(literal)
    elif value_type == 'decimal' and literal.find('.') == -1:
        return int(literal)
    elif value_type in ('decimal', 'float', 'double'):
        return float(literal)
    elif value_type in ('string'):
        return literal
    elif value_type in ('dateTime'):
        try:
            return datetime.strptime(literal, ISOFORMAT_MS)
        except ValueError:
            return datetime.strptime(literal, ISOFORMAT_SHORT)
    return literal


def get_node_type(node):
    """Return just the base name of a XSD datatype:
    e.g. http://www.w3.org/2001/XMLSchema#integer -> integer
    """
    # chop off xml schema declaration
    value_type = node.literal_value['datatype']
    if value_type is None:
        return "string"
    else:
        value_type = str(value_type)
        return value_type.replace(str(xsdNS[''].uri), '')


def simplify_rdf(value):
    """Return a short name for a RDF object
    e.g. The last part of a URI or an untyped string.
    """
    if isinstance(value, RDF.Node):
        if value.is_resource():
            name = simplify_uri(str(value.uri))
        elif value.is_blank():
            name = '<BLANK>'
        else:
            name = value.literal_value['string']
    elif isinstance(value, RDF.Uri):
        name = split_uri(str(value))
    else:
        name = value
    return str(name)


def simplify_uri(uri):
    """Split off the end of a uri

    >>> simplify_uri('http://asdf.org/foo/bar')
    'bar'
    >>> simplify_uri('http://asdf.org/foo/bar#bleem')
    'bleem'
    >>> simplify_uri('http://asdf.org/foo/bar/')
    'bar'
    >>> simplify_uri('http://asdf.org/foo/bar?was=foo')
    'was=foo'
    """
    if isinstance(uri, RDF.Node):
        if uri.is_resource():
            uri = uri.uri
        else:
            raise ValueError("Can't simplify an RDF literal")
    if isinstance(uri, RDF.Uri):
        uri = str(uri)

    parsed = urllib.parse.urlparse(uri)
    if len(parsed.query) > 0:
        return parsed.query
    elif len(parsed.fragment) > 0:
        return parsed.fragment
    elif len(parsed.path) > 0:
        for element in reversed(parsed.path.split('/')):
            if len(element) > 0:
                return element
    raise ValueError("Unable to simplify %s" % (uri,))

def strip_namespace(namespace, term):
    """Remove the namespace portion of a term

    returns None if they aren't in common
    """
    if isinstance(term, RDF.Node):
        if  term.is_resource():
            term = term.uri
        else:
            raise ValueError("This works on resources")
    elif not isinstance(term, RDF.Uri):
        raise ValueError("This works on resources")
    term_s = str(term)
    if not term_s.startswith(namespace._prefix):
        return None
    return term_s.replace(namespace._prefix, "")


def get_model(model_name=None, directory=None, use_contexts=True):
    if directory is None:
        directory = os.getcwd()

    contexts = 'yes' if use_contexts else 'no'

    if model_name is None:
        storage = RDF.MemoryStorage(options_string="contexts='{}'".format(contexts))
        logger.info("Using RDF Memory model")
    else:
        options = "contexts='{0}',hash-type='bdb',dir='{1}'".format(contexts, directory)
        storage = RDF.HashStorage(model_name,
                      options=options)
        logger.info("Using {0} with options {1}".format(model_name, options))
    model = RDF.Model(storage)
    return model


def load_into_model(model, parser_name, path, ns=None):
    if isinstance(ns, six.string_types):
        ns = RDF.Uri(ns)

    if isinstance(path, RDF.Node):
        if path.is_resource():
            path = str(path.uri)
        else:
            raise ValueError("url to load can't be a RDF literal")

    url_parts = list(urllib.parse.urlparse(path))
    if len(url_parts[0]) == 0 or url_parts[0] == 'file':
        url_parts[0] = 'file'
        url_parts[2] = os.path.abspath(url_parts[2])
    if parser_name is None or parser_name == 'guess':
        parser_name = guess_parser_by_extension(path)
    url = urllib.parse.urlunparse(url_parts)
    logger.info("Opening {0} with parser {1}".format(url, parser_name))

    rdf_parser = RDF.Parser(name=parser_name)

    statements = []
    retries = 3
    succeeded = False
    while retries > 0:
        try:
            retries -= 1
            statements = rdf_parser.parse_as_stream(url, ns)
            retries = 0
            succeeded = True
        except RDF.RedlandError as e:
            errmsg = "RDF.RedlandError: {0} {1} tries remaining"
            logger.error(errmsg.format(str(e), retries))

    if not succeeded:
        logger.warn("Unable to download %s", url)

    for s in statements:
        conditionally_add_statement(model, s, ns)

def load_string_into_model(model, parser_name, data, ns=None):
    ns = fixup_namespace(ns)
    logger.debug("load_string_into_model parser={0}, len={1}".format(
        parser_name, len(data)))
    rdf_parser = RDF.Parser(name=str(parser_name))

    for s in rdf_parser.parse_string_as_stream(data, ns):
        conditionally_add_statement(model, s, ns)


def fixup_namespace(ns):
    if ns is None:
        ns = RDF.Uri("http://localhost/")
    elif isinstance(ns, six.string_types):
        ns = RDF.Uri(ns)
    elif not(isinstance(ns, RDF.Uri)):
        errmsg = "Namespace should be string or uri not {0}"
        raise ValueError(errmsg.format(str(type(ns))))
    return ns


def conditionally_add_statement(model, s, ns):
    imports = owlNS['imports']
    if s.predicate == imports:
        obj = str(s.object)
        logger.info("Importing %s" % (obj,))
        load_into_model(model, None, obj, ns)
    if s.object.is_literal():
        value_type = get_node_type(s.object)
        if value_type == 'string':
            s.object = sanitize_literal(s.object)
    model.add_statement(s)


def add_default_schemas(model, schema_path=None):
    """Add default schemas to a model
    Looks for turtle files in either htsworkflow/util/schemas
    or in the list of directories provided in schema_path
    """

    schemas = resource_listdir(__name__, 'schemas')
    for s in schemas:
        schema = resource_string(__name__,  'schemas/' + s)
        if six.PY3:
            # files must be encoded utf-8
            schema = schema.decode('utf-8')
        namespace = 'file://localhost/htsworkflow/schemas/'+s
        add_schema(model, schema, namespace)

    if schema_path:
        if type(schema_path) in types.StringTypes:
            schema_path = [schema_path]

        for path in schema_path:
            for pathname in glob(os.path.join(path, '*.turtle')):
                url = 'file://' + os.path.splitext(pathname)[0]
                stream = open(pathname, 'rt')
                add_schema(model, stream, url)
                stream.close()

def add_schema(model, schema, url):
    """Add a schema to a model.

    Main difference from 'load_into_model' is it tags it with
    a RDFlib context so I can remove them later.
    """
    parser = RDF.Parser(name='turtle')
    context = RDF.Node(RDF.Uri(SCHEMAS_URL))
    for s in parser.parse_string_as_stream(schema, url):
        try:
            model.append(s, context)
        except RDF.RedlandError as e:
            logger.error("%s with %s", str(e), str(s))


def remove_schemas(model):
    """Remove statements labeled with our schema context"""
    context = RDF.Node(RDF.Uri(SCHEMAS_URL))
    model.context_remove_statements(context)


def sanitize_literal(node):
    """Clean up a literal string
    """
    if not isinstance(node, RDF.Node):
        raise ValueError("sanitize_literal only works on RDF.Nodes")

    s = node.literal_value['string']
    if len(s) > 0:
        element = lxml.html.fromstring(s)
        cleaner = lxml.html.clean.Cleaner(page_structure=False)
        element = cleaner.clean_html(element)
        if six.PY3:
            text = lxml.html.tostring(element, encoding=str)
        else:
            text = lxml.html.tostring(element)
        p_len = 3
        slash_p_len = 4

        args = {'literal': text[p_len:-slash_p_len]}
    else:
        args = {'literal': ''}
    datatype = node.literal_value['datatype']
    if datatype is not None:
        args['datatype'] = datatype
    language = node.literal_value['language']
    if language is not None:
        args['language'] = language
    return RDF.Node(**args)


def guess_parser(content_type, pathname):
    if content_type in ('application/rdf+xml',):
        return 'rdfxml'
    elif content_type in ('application/x-turtle',):
        return 'turtle'
    elif content_type in ('text/html',):
        return 'rdfa'
    elif content_type is None or content_type in ('text/plain',):
        return guess_parser_by_extension(pathname)

def guess_parser_by_extension(pathname):
    _, ext = os.path.splitext(pathname)
    if ext in ('.xml', '.rdf'):
        return 'rdfxml'
    elif ext in ('.html',):
        return 'rdfa'
    elif ext in ('.turtle',):
        return 'turtle'
    return 'guess'

def get_serializer(name='turtle'):
    """Return a serializer with our standard prefixes loaded
    """
    writer = RDF.Serializer(name=name)
    # really standard stuff
    writer.set_namespace('rdf', rdfNS._prefix)
    writer.set_namespace('rdfs', rdfsNS._prefix)
    writer.set_namespace('owl', owlNS._prefix)
    writer.set_namespace('dc', dcNS._prefix)
    writer.set_namespace('xml', xmlNS._prefix)
    writer.set_namespace('xsd', xsdNS._prefix)
    writer.set_namespace('vs', vsNS._prefix)
    writer.set_namespace('wot', wotNS._prefix)

    # should these be here, kind of specific to an application
    writer.set_namespace('htswlib', libraryOntology._prefix)
    writer.set_namespace('ucscSubmission', submissionOntology._prefix)
    writer.set_namespace('ucscDaf', dafTermOntology._prefix)
    writer.set_namespace('geoSoft', geoSoftNS._prefix)
    writer.set_namespace('encode3', encode3NS._prefix)
    return writer

def get_turtle_header():
    """Return a turtle header with our typical namespaces
    """
    serializer = get_serializer()
    empty = get_model()
    return serializer.serialize_model_to_string(empty)

def dump_model(model, destination=None):
    if destination is None:
        destination = sys.stdout
    serializer = get_serializer()
    destination.write(serializer.serialize_model_to_string(model))
    destination.write(os.linesep)
