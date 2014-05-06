from unittest import TestCase, TestSuite, defaultTestLoader, skip

from htsworkflow.util.rdfjsonld import load_into_model, to_node, triple_to_statement
from htsworkflow.util.rdfhelp import get_model

jstatement = {
    'object': {'datatype': u'http://www.w3.org/2001/XMLSchema#dateTime',
                'type': 'literal',
                'value': '1940-10-09'},
    'predicate': {'type': 'IRI',
                    'value': u'http://schema.org/birthDate'},
    'subject': {'type': 'blank node',
                'value': '_:a'}
}
doc = {
  "@context": "http://json-ld.org/contexts/person.jsonld",
  "@id": "http://dbpedia.org/resource/John_Lennon",
  "name": "John Lennon",
  "born": "1940-10-09",
  "spouse": "http://dbpedia.org/resource/Cynthia_Lennon"
}

class TestJsonLD(TestCase):
    def test_to_node(self):
        obj = to_node(jstatement['object'])
        self.assertTrue(obj.is_literal())
        self.assertEqual(str(obj), '1940-10-09')
        pred = to_node(jstatement['predicate'])
        self.assertTrue(pred.is_resource())
        self.assertEqual(str(pred.uri), jstatement['predicate']['value'])
        subj = to_node(jstatement['subject'])
        self.assertTrue(subj.is_blank())

    def test_to_statement(self):
        stmt = triple_to_statement(jstatement)
        self.assertTrue(stmt.object.is_literal())
        self.assertEqual(str(stmt.object), '1940-10-09')
        self.assertTrue(stmt.predicate.is_resource())
        self.assertEqual(str(stmt.predicate.uri), jstatement['predicate']['value'])
        self.assertTrue(stmt.subject.is_blank())

    def test_load_model(self):
        model = get_model(use_contexts=False)
        self.assertEqual(len(model), 0)
        load_into_model(model, doc)
        self.assertEqual(len(model), 3)

def suite():
    suite = TestSuite()
    suite.addTests(
        defaultTestLoader.loadTestsFromTestCase(TestJsonLD))
    return suite

if __name__ == "__main__":
    from unittest import main
    main(defaultTest='suite')
