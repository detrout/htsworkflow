"""Helper features for working with librdf
"""
from datetime import datetime
import logging
import os
import types

import RDF

logger = logging.getLogger(__name__)

# standard ontology namespaces
owlNS = RDF.NS('http://www.w3.org/2002/07/owl#')
dublinCoreNS = RDF.NS("http://purl.org/dc/elements/1.1/")
rdfNS = RDF.NS("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rdfsNS= RDF.NS("http://www.w3.org/2000/01/rdf-schema#")
xsdNS = RDF.NS("http://www.w3.org/2001/XMLSchema#")

# internal ontologies
submissionOntology = RDF.NS("http://jumpgate.caltech.edu/wiki/UcscSubmissionOntology#")
dafTermOntology = RDF.NS("http://jumpgate.caltech.edu/wiki/UcscDaf#")
libraryOntology = RDF.NS("http://jumpgate.caltech.edu/wiki/LibraryOntology#")
inventoryOntology = RDF.NS("http://jumpgate.caltech.edu/wiki/InventoryOntology#")
submissionLog = RDF.NS("http://jumpgate.caltech.edu/wiki/SubmissionsLog/")

ISOFORMAT_MS = "%Y-%m-%dT%H:%M:%S.%f"
ISOFORMAT_SHORT = "%Y-%m-%dT%H:%M:%S"

def sparql_query(model, query_filename):
    """Execute sparql query from file
    """
    logger.info("Opening: %s" % (query_filename,))
    query_body = open(query_filename,'r').read()
    query = RDF.SPARQLQuery(query_body)
    results = query.execute(model)
    display_query_results(results)

def display_query_results(results):
    for row in results:
        output = []
        for k,v in row.items()[::-1]:
            print "{0}: {1}".format(k,v)
        print


def blankOrUri(value=None):
    node = None
    if value is None:
        node = RDF.Node()
    elif type(value) in types.StringTypes:
        node = RDF.Node(uri_string=value)
    elif isinstance(value, RDF.Node):
        node = value

    return node


def toTypedNode(value):
    if type(value) == types.BooleanType:
        value_type = xsdNS['boolean'].uri
        if value:
            value = u'1'
        else:
            value = u'0'
    elif type(value) in (types.IntType, types.LongType):
        value_type = xsdNS['decimal'].uri
        value = unicode(value)
    elif type(value) == types.FloatType:
        value_type = xsdNS['float'].uri
        value = unicode(value)
    elif isinstance(value, datetime):
        value_type = xsdNS['dateTime'].uri
        if value.microsecond == 0:
            value = value.strftime(ISOFORMAT_SHORT)
        else:
            value = value.strftime(ISOFORMAT_MS)
    else:
        value_type = None
        value = unicode(value)

    if value_type is not None:
        node = RDF.Node(literal=value, datatype=value_type)
    else:
        node = RDF.Node(literal=unicode(value).encode('utf-8'))
    return node

def fromTypedNode(node):
    if node is None:
        return None

    value_type = str(node.literal_value['datatype'])
    # chop off xml schema declaration
    value_type = value_type.replace(str(xsdNS[''].uri),'')
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
        except ValueError, e:
            return datetime.strptime(literal, ISOFORMAT_SHORT)
    return literal


def get_model(model_name=None, directory=None):
    if directory is None:
        directory = os.getcwd()

    if model_name is None:
        storage = RDF.MemoryStorage()
        logger.info("Using RDF Memory model")
    else:
        options = "hash-type='bdb',dir='{0}'".format(directory)
        storage = RDF.HashStorage(model_name,
                      options=options)
        logger.info("Using {0} with options {1}".format(model_name, options))
    model = RDF.Model(storage)
    return model


def load_into_model(model, parser_name, filename, ns=None):
    if not os.path.exists(filename):
        raise IOError("Can't find {0}".format(filename))

    data = open(filename, 'r').read()
    load_string_into_model(model, parser_name, data, ns)


def load_string_into_model(model, parser_name, data, ns=None):
    if ns is None:
        ns = "http://localhost/"

    rdf_parser = RDF.Parser(name=parser_name)
    rdf_parser.parse_string_into_model(model, data, ns)


def get_serializer(name='turtle'):
    """Return a serializer with our standard prefixes loaded
    """
    writer = RDF.Serializer(name=name)
    # really standard stuff
    writer.set_namespace('owl', owlNS._prefix)
    writer.set_namespace('rdf', rdfNS._prefix)
    writer.set_namespace('rdfs', rdfsNS._prefix)
    writer.set_namespace('xsd', xsdNS._prefix)

    # should these be here, kind of specific to an application
    writer.set_namespace('libraryOntology', libraryOntology._prefix)
    writer.set_namespace('ucscSubmission', submissionOntology._prefix)
    writer.set_namespace('ucscDaf', dafTermOntology._prefix)
    return writer

def dump_model(model):
    serializer = get_serializer()
    print serializer.serialize_model_to_string(model)
