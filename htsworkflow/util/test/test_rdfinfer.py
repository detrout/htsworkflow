from unittest import TestCase

from rdflib import ConjunctiveGraph, Literal, Namespace

from encoded_client.rdfhelp import add_default_schemas
from encoded_client.rdfns import RDF, RDFS, DC
from htsworkflow.util.rdfinfer import Infer

from rdflib.namespace import FOAF

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

class TestInfer(TestCase):
    def setUp(self):
        self.model = ConjunctiveGraph()
        add_default_schemas(self.model)
        self.model.parse(data=MINI_FOAF_ONTOLOGY, format='turtle')

    def test_class(self):
        fooNS = Namespace('http://example.org/')
        self.model.parse(data=FOAF_DATA, format='turtle')
        inference = Infer(self.model)

        s = [fooNS['me.jpg'], RDF['type'], RDFS['Class']]
        found = list(self.model.triples(s))
        self.assertEqual(len(found), 0)
        inference._rule_class()
        s = [fooNS['me.jpg'], RDF['type'], RDFS['Class']]
        found = list(self.model.triples(s))
        self.assertEqual(len(found), 1)

    def test_inverse_of(self):
        fooNS = Namespace('http://example.org/')
        self.model.parse(data=FOAF_DATA, format='turtle')
        inference = Infer(self.model)
        depiction = (None, FOAF['depiction'], fooNS['me.jpg'])
        size = len(self.model)
        found_statements = list(self.model.triples(depiction))
        self.assertEqual(len(found_statements), 0)
        inference._rule_inverse_of()
        found_statements = list(self.model.triples(depiction))
        self.assertEqual(len(found_statements), 1)

        # we should've added one statement.
        self.assertEqual(len(self.model), size + 1)

        size = len(self.model)
        inference._rule_inverse_of()
        # we should already have both versions in our model
        self.assertEqual(len(self.model), size)

    def test_validate_types(self):
        fooNS = Namespace('http://example.org/')
        self.model.parse(data=FOAF_DATA, format='turtle')
        inference = Infer(self.model)

        errors = list(inference._validate_types())
        self.assertEqual(len(errors), 0)

        s = (fooNS['document'], DC['title'], Literal("bleem"))
        self.model.add(s)
        errors = list(inference._validate_types())
        self.assertEqual(len(errors), 1)

    def test_validate_undefined_properties_in_schemas(self):
        fooNS = Namespace('http://example.org/')
        inference = Infer(self.model)

        errors = list(inference._validate_undefined_properties())
        self.assertEqual(len(errors), 0)

    def test_validate_undefined_properties_in_inference(self):
        fooNS = Namespace('http://example.org/')
        foafNS = Namespace('http://xmlns.com/foaf/0.1/')

        self.model.parse(data=FOAF_DATA, format='turtle')

        inference = Infer(self.model)
        errors = list(inference._validate_undefined_properties())
        self.assertEqual(len(errors), 2)

        inference = Infer(self.model)
        errors = list(inference._validate_property_types())
        self.assertEqual(len(errors), 0)

        s = (fooNS['me.jpg'], FOAF['firstName'], Literal("name"))
        self.model.add(s)
        errors = list(inference._validate_property_types())
        self.assertEqual(len(errors), 1)
        startswith = 'Domain of '
        self.assertEqual(errors[0][:len(startswith)], startswith)
        self.assertTrue('http://example.org/me.jpg' in errors[0])
        endswith = 'http://xmlns.com/foaf/0.1/Person'
        self.assertEqual(errors[0][-len(endswith):], endswith)
        self.model.remove(s)

        errors = list(inference._validate_property_types())
        self.assertEqual(len(errors), 0)
        s = (fooNS['foo.txt'], RDF['type'], FOAF['Document'])
        self.model.add(s)
        s = (fooNS['me.jpg'], FOAF['depicts'], FOAF['Document'])
        self.model.add(s)

        errors = list(inference._validate_property_types())
        self.assertEqual(len(errors), 1)
        startswith = 'Range of '
        self.assertEqual(errors[0][:len(startswith)], startswith)
        self.assertTrue('http://example.org/me.jpg' in errors[0])
        endswith = 'http://www.w3.org/2002/07/owl#Thing'
        self.assertEqual(errors[0][-len(endswith):], endswith)
        self.model.remove(s)

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
        self.model.parse(data=turtle, format='turtle')
        inference = Infer(self.model)

        errmsg = list(inference._validate_property_types())
        self.assertEqual(len(errmsg), 0)


def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestInfer))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
