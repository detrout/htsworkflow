"""Helper features for working with librdf
"""
import os
import types

import RDF

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
submissionLog = RDF.NS("http://jumpgate.caltech.edu/wiki/SubmissionsLog/")

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
    elif type(value) in types.StringTypes:
        value_type = xsdNS['string'].uri
    else:
        value_type = None
        value = unicode(value)

    return RDF.Node(literal=value, datatype=value_type)

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
    elif value_type == 'decimal' and literal.find('.') == -1:
        return int(literal)
    elif value_type in ('decimal', 'float', 'double'):
        return float(literal)
    elif value_type in ('string'):
        return literal
    elif value_type in ('dateTime'):
        raise NotImplemented('need to parse isoformat date-time')

    return literal


def get_model(model_name=None, directory=None):
    if directory is None:
        directory = os.getcwd()
        
    if model_name is None:
        storage = RDF.MemoryStorage()
    else:
        storage = RDF.HashStorage(model_name,
                      options="hash-type='bdb',dir='{0}'".format(directory))
    model = RDF.Model(storage)
    return model
        

def load_into_model(model, parser_name, filename, ns=None):
    if not os.path.exists(filename):
        raise IOError("Can't find {0}".format(filename))
    
    data = open(filename, 'r').read()
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

