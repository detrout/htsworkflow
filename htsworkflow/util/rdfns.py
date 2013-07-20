"""Namespace definitions

All in one place to make import rdfns.* work safely
"""
from RDF import NS

# standard ontology namespaces
rdfNS = NS("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rdfsNS = NS("http://www.w3.org/2000/01/rdf-schema#")
owlNS = NS('http://www.w3.org/2002/07/owl#')
dcNS = NS("http://purl.org/dc/elements/1.1/")
xmlNS = NS('http://www.w3.org/XML/1998/namespace')
xsdNS = NS("http://www.w3.org/2001/XMLSchema#")
vsNS = NS('http://www.w3.org/2003/06/sw-vocab-status/ns#')
wotNS = NS('http://xmlns.com/wot/0.1/')

# internal ontologies
submissionOntology = NS(
    "http://jumpgate.caltech.edu/wiki/UcscSubmissionOntology#")
dafTermOntology = NS("http://jumpgate.caltech.edu/wiki/UcscDaf#")
libraryOntology = NS("http://jumpgate.caltech.edu/wiki/LibraryOntology#")
inventoryOntology = NS(
    "http://jumpgate.caltech.edu/wiki/InventoryOntology#")
submissionLog = NS("http://jumpgate.caltech.edu/wiki/SubmissionsLog/")
geoSoftNS = NS('http://www.ncbi.nlm.nih.gov/geo/info/soft2.html#')
encode3NS = NS("http://jumpgate.caltech.edu/wiki/Encode3#")
