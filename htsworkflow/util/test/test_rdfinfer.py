import unittest

import RDF

from htsworkflow.util.rdfhelp import get_model, \
     add_default_schemas, add_schema, load_string_into_model, dump_model
from htsworkflow.util.rdfns import *
from htsworkflow.util.rdfinfer import Infer

foafNS = RDF.NS('http://xmlns.com/foaf/0.1/')

MINI_FOAF_ONTOLOGY = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .


foaf:Agent
     a rdfs:Class, owl:Class ;
     rdfs:comment "An agent (person, group, software or physical artifiact)."@en;
     rdfs:label "Agent" .

foaf:Person
     a rdfs:Class, owl:Class, foaf:Agent ;
     rdfs:label "Person" .

foaf:age
     a rdf:Property, owl:DatatypeProperty, owl:FunctionalProperty ;
     rdfs:comment "The age in years of some agent." ;
     rdfs:domain foaf:Agent ;
     rdfs:label "age";
     rdfs:range rdfs:Literal .

foaf:familyName
     a rdf:Property, owl:DatatypeProperty ;
     rdfs:comment "Family name of some person." ;
     rdfs:label "familyName" ;
     rdfs:domain foaf:Person ;
     rdfs:range rdfs:Literal .

foaf:firstName
     a rdf:Property, owl:DatatypeProperty ;
     rdfs:comment "the first name of a person." ;
     rdfs:domain foaf:Person ;
     rdfs:label "firstname" ;
     rdfs:range rdfs:Literal .

foaf:Document
     a rdfs:Class, owl:Class ;
     rdfs:comment "A document." .

foaf:Image
     a rdfs:Class, owl:Class ;
     rdfs:comment "An image." ;
     rdfs:subClassOf foaf:Document .

foaf:depicts
     a rdf:Property, owl:ObjectProperty ;
     rdfs:comment "A thing depicted in this representation." ;
     rdfs:domain foaf:Image ;
     rdfs:range owl:Thing ;
     owl:inverseOf foaf:depiction .

foaf:depiction
     a rdf:Property, owl:ObjectProperty ;
     rdfs:comment "Depiction of some thing." ;
     rdfs:domain owl:Thing ;
     rdfs:range foaf:Image ;
     owl:inverseOf foaf:depicts .
"""

FOAF_DATA = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

_:me
     foaf:firstName "Diane" ;
     foaf:familyName "Trout" ;
     a foaf:Person, owl:Thing ;
     <http://example.org/other_literal> "value" ;
     <http://example.org/other_resource> <http://example.org/resource> .

<http://example.org/me.jpg>
     a foaf:Image, owl:Thing ;
     foaf:depicts _:me .
"""

class TestInfer(unittest.TestCase):
    def setUp(self):
        self.model = get_model()
        add_default_schemas(self.model)
        load_string_into_model(self.model, 'turtle', MINI_FOAF_ONTOLOGY)

    def test_class(self):
        fooNS = RDF.NS('http://example.org/')
        load_string_into_model(self.model, 'turtle', FOAF_DATA)
        inference = Infer(self.model)

        s = RDF.Statement(fooNS['me.jpg'], rdfNS['type'], rdfsNS['Class'])
        found = list(self.model.find_statements(s))
        self.assertEqual(len(found), 0)
        inference._rule_class()
        s = RDF.Statement(fooNS['me.jpg'], rdfNS['type'], rdfsNS['Class'])
        found = list(self.model.find_statements(s))
        self.assertEqual(len(found), 1)

    def test_inverse_of(self):
        fooNS = RDF.NS('http://example.org/')
        load_string_into_model(self.model, 'turtle', FOAF_DATA)
        inference = Infer(self.model)
        depiction = RDF.Statement(None,
                                  foafNS['depiction'],
                                  fooNS['me.jpg'])
        size = self.model.size()
        found_statements = list(self.model.find_statements(depiction))
        self.assertEqual(len(found_statements), 0)
        inference._rule_inverse_of()
        found_statements = list(self.model.find_statements(depiction))
        self.assertEqual(len(found_statements), 1)

        # we should've added one statement.
        self.assertEqual(self.model.size(), size + 1)

        size = self.model.size()
        inference._rule_inverse_of()
        # we should already have both versions in our model
        self.assertEqual(self.model.size(), size)

    def test_validate_types(self):
        fooNS = RDF.NS('http://example.org/')
        load_string_into_model(self.model, 'turtle', FOAF_DATA)
        inference = Infer(self.model)

        errors = list(inference._validate_types())
        self.assertEqual(len(errors), 0)

        s = RDF.Statement(fooNS['document'],
                          dcNS['title'],
                          RDF.Node("bleem"))
        self.model.append(s)
        errors = list(inference._validate_types())
        self.assertEqual(len(errors), 1)

    def test_validate_undefined_properties(self):
        fooNS = RDF.NS('http://example.org/')
        inference = Infer(self.model)

        errors = list(inference._validate_undefined_properties())
        self.assertEqual(len(errors), 0)

        load_string_into_model(self.model, 'turtle', FOAF_DATA)

        errors = list(inference._validate_undefined_properties())
        self.assertEqual(len(errors), 2)


    def test_validate_undefined_properties(self):
        fooNS = RDF.NS('http://example.org/')
        foafNS = RDF.NS('http://xmlns.com/foaf/0.1/')
        load_string_into_model(self.model, 'turtle', FOAF_DATA)
        inference = Infer(self.model)

        errors = list(inference._validate_property_types())
        self.assertEqual(len(errors), 0)

        s = RDF.Statement(fooNS['me.jpg'],
                          foafNS['firstName'],
                          RDF.Node("name"))
        self.model.append(s)
        errors = list(inference._validate_property_types())
        self.assertEqual(len(errors), 1)
        startswith = 'Domain of '
        self.assertEqual(errors[0][:len(startswith)], startswith)
        self.assertTrue('http://example.org/me.jpg' in errors[0])
        endswith = 'http://xmlns.com/foaf/0.1/Person'
        self.assertEqual(errors[0][-len(endswith):], endswith)
        del self.model[s]

        errors = list(inference._validate_property_types())
        self.assertEqual(len(errors), 0)
        s = RDF.Statement(fooNS['foo.txt'], rdfNS['type'], foafNS['Document'])
        self.model.append(s)
        s = RDF.Statement(fooNS['me.jpg'],
                          foafNS['depicts'],
                          foafNS['foo.txt'])
        self.model.append(s)

        errors = list(inference._validate_property_types())
        self.assertEqual(len(errors), 1)
        startswith = 'Range of '
        self.assertEqual(errors[0][:len(startswith)], startswith)
        self.assertTrue('http://example.org/me.jpg' in errors[0])
        endswith = 'http://www.w3.org/2002/07/owl#Thing'
        self.assertEqual(errors[0][-len(endswith):], endswith)
        del self.model[s]

    def test_property_multiple_domain_types(self):
        """Can we process a property with multiple domain types?
        """
        turtle = """
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix foo: <http://example.org/> .
        @prefix bar: <http://example.com/> .

        foo:AClass a rdfs:Class .
        foo:BClass a rdfs:Class .
        bar:ABarClass a rdfs:Class .

        foo:aprop a rdf:Property ;
            rdfs:domain foo:AClass ;
            rdfs:domain bar:ABarClass ;
            rdfs:range foo:BClass .

        foo:object a foo:BClass .
        foo:subject a foo:AClass ;
           foo:aprop foo:object .
        bar:subject a bar:ABarClass ;
           foo:aprop foo:object .
        """
        load_string_into_model(self.model, 'turtle', turtle)
        inference = Infer(self.model)

        errmsg = list(inference._validate_property_types())
        print errmsg
        self.failUnlessEqual(len(errmsg), 0)

def suite():
    return unittest.makeSuite(TestInfer, 'test')

if __name__ == "__main__":
    unittest.main(defaultTest='suite')
