import RDF

from htsworkflow.util.rdfns import *
from htsworkflow.util.rdfhelp import SCHEMAS_URL

INFER_URL='http://jumpgate.caltech.edu/phony/infer'

class Infer(object):
    """Provide some simple inference.

    Provides a few default rules as methods starting with _rule_
    """
    def __init__(self, model):
        self.model = model
        self._context = RDF.Node(RDF.Uri(INFER_URL))


    def update(self, max_iterations=None):
        """Update model with with inferred statements.

        max_iterations puts a limit on the number of times we
        run through the loop.

        it will also try to exit if nothing new has been inferred.

        Also this is the naive solution.
        There's probably better ones out there.
        """
        iterations = 0
        while max_iterations is None or iterations != max_iterations:
            starting_size = self.model.size()

            for method_name in dir(self):
                if method_name.startswith('_rule_'):
                    method = getattr(self, method_name)
                    method()
            if self.model.size() == starting_size:
                # we didn't add anything new
                return

    def _rule_inverse_of(self):
        """Add statements computed with inverseOf
        """
        body = """
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        prefix owl: <http://www.w3.org/2002/07/owl#>

        select ?o ?reverse ?s
        where  {
            ?s ?term ?o .
            ?s a ?subject_type .
            ?o a ?object_type .
            ?term owl:inverseOf ?reverse .
            ?term rdfs:domain ?subject_type ;
                  rdfs:range ?object_type .
            ?reverse rdfs:domain ?object_type ;
                  rdfs:range ?subject_type .
        }"""
        query = RDF.SPARQLQuery(body)

        statements = []
        for r in query.execute(self.model):
            s = RDF.Statement(r['o'], r['reverse'], r['s'])
            if s not in self.model:
                self.model.append(s, self._context)


    def _validate_types(self):
        body = """
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        prefix owl: <http://www.w3.org/2002/07/owl#>

        select ?subject ?predicate ?object
        where {
          ?subject ?predicate ?object
          OPTIONAL { ?subject a ?class }
          FILTER(!bound(?class))
        }
        """
        query = RDF.SPARQLQuery(body)
        errmsg = "Missing type for: {0}"
        for r in query.execute(self.model):
            yield errmsg.format(str(r['subject']))

    def _validate_undefined_properties(self):
        """Find properties that aren't defined.
        """
        body = """
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        prefix owl: <http://www.w3.org/2002/07/owl#>

        select ?subject ?predicate ?object
        where {
            ?subject ?predicate ?object
            OPTIONAL { ?predicate a ?predicate_class }
            FILTER(!bound(?predicate_class))
        }"""
        query = RDF.SPARQLQuery(body)
        msg = "Undefined property in {0} {1} {2}"
        for r in query.execute(self.model):
            yield msg.format(str(r['subject']),
                             str(r['predicate']),
                             str(r['object']))

    def _validate_property_types(self):
        """Find resources that don't have a type
        """
        property_template = """
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        select ?type
        where {{
            <{predicate}> a rdf:Property ;
                        {space} ?type .
        }}"""

        wrong_domain_type = "Domain of {0} {1} {2} not {3}"
        wrong_range_type = "Range of {0} {1} {2} not {3}"

        count = 0
        schema = RDF.Node(RDF.Uri(SCHEMAS_URL))
        for s, context in self.model.as_stream_context():
            if context == schema:
                continue
            # check domain
            query = RDF.SPARQLQuery(property_template.format(
                predicate=s.predicate,
                space='rdfs:domain'))
            for r in query.execute(self.model):
                if r['type'] == rdfsNS['Resource']:
                    continue
                check = RDF.Statement(s.subject, rdfNS['type'], r['type'])
                if not self.model.contains_statement(check):
                    yield wrong_domain_type.format(str(s.subject),
                                                   str(s.predicate),
                                                   str(s.object),
                                                   str(r['type']))
            # check range
            query = RDF.SPARQLQuery(property_template.format(
                predicate=s.predicate,
                space='rdfs:range'))
            for r in query.execute(self.model):
                if r['type'] == rdfsNS['Resource']:
                    continue
                check = RDF.Statement(s.object, rdfNS['type'], r['type'])
                if not self.model.contains_statement(check):
                    yield wrong_range_type.format(str(s.subject),
                                                  str(s.predicate),
                                                  str(s.object),
                                                  str(r['type']))

        return
