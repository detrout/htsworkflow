"""Helper features for working with librdf
"""
import RDF
import types

# standard ontology namespaces
dublinCoreNS = RDF.NS("http://purl.org/dc/elements/1.1/")
rdfNS = RDF.NS("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rdfsNS= RDF.NS("http://www.w3.org/2000/01/rdf-schema#")
xsdNS = RDF.NS("http://www.w3.org/2001/XMLSchema#")

# internal ontologies
submitOntology = RDF.NS("http://jumpgate.caltech.edu/wiki/UCSCSubmissionOntology#")
libraryOntology = RDF.NS("http://jumpgate.caltech.edu/wiki/LibraryOntology#")

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
    elif type(value) in types.StringTypes:
        value_type = xsdNS['string'].uri
    else:
        value_type = None
        value = unicode(value)

    return RDF.Node(literal=value, datatype=value_type)
    
