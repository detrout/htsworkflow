import logging
import os
import sys

from rdflib import ConjunctiveGraph, BNode, Literal, URIRef
from rdflib.plugins.sparql import prepareQuery

from htsworkflow.util.rdfns import *
from htsworkflow.util.rdfhelp import SCHEMAS_URL

INFER_URL='http://jumpgate.caltech.edu/phony/infer'
LOGGER = logging.getLogger(__name__)

class Infer(object):
    """Provide some simple inference.

    Provides a few default rules as methods starting with _rule_
    """
    def __init__(self, model):
        if not isinstance(model, ConjunctiveGraph):
            raise ValueError("Inferences require a ConjunctiveGraph")

        self.model = model
        self._context = URIRef(INFER_URL)


    def think(self, max_iterations=None):
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
                    LOGGER.info("Running: %s", method_name)
                    method = getattr(self, method_name)
                    method()
            if self.model.size() == starting_size:
                # we didn't add anything new
                return

    def validate(self, destination=None):
        if destination is None:
            destination = sys.stdout

        for msg in self.run_validation():
            destination.write(msg)
            destination.write(os.linesep)

    def run_validation(self):
        """Apply validation rules to our model.
        """
        for method_name in dir(self):
            if method_name.startswith('_validate_'):
                LOGGER.info("Running: %s", method_name)
                method = getattr(self, method_name)
                for msg in method():
                    yield msg

    def _rule_class(self):
        """resolve class chains.
        e.g. if a is an BClass, and a BClass is an AClass
        then a is both a BClass and AClass.
        """
        body = """
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        prefix owl: <http://www.w3.org/2002/07/owl#>

        select ?obj ?class
        where  {
          ?alias a ?class .
          ?obj a ?alias .
        }"""
        for r in self.model.query(body):
            s = (r['obj'], RDF['type'], r['class'], self._context)
            if s not in self.model:
                self.model.add(s)

    def _rule_subclass(self):
        """A subclass is a parent class
        """
        body = """
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        prefix owl: <http://www.w3.org/2002/07/owl#>

        select ?obj ?subclass ?parent
        where  {
          ?subclass rdfs:subClassOf ?parent .
          ?obj a ?subclass .
        }"""
        for r in self.model.query(body):
            s = (r['obj'], RDF['type'], r['parent'], self._context)
            if s not in self.model:
                self.model.add(s)

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
        for r in self.model.query(body):
            s = (r['o'], r['reverse'], r['s'], self._context)
            if s not in self.model:
                self.model.add(s)

    def _validate_types(self):
        body = """
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        prefix owl: <http://www.w3.org/2002/07/owl#>
        prefix xhtmlv: <http://www.w3.org/1999/xhtml/vocab#>

        select ?subject ?predicate ?object
        where {
          ?subject ?predicate ?object
          OPTIONAL { ?subject a ?class }
          FILTER(!bound(?class))
          FILTER(?predicate != xhtmlv:stylesheet)
        }
        """
        errmsg = "Missing type for: {0}"
        for r in self.model.query(body):
            yield errmsg.format(str(r[0]))

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
        msg = "Undefined property in {0} {1} {2}"
        for r in self.model.query(body):
            yield msg.format(r['subject'],
                             r['predicate'],
                             r['object'])

    def _validate_property_types(self):
        """Find resources that don't have a type
        """
        property_query = prepareQuery("""
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        select ?type ?predicate
        where {
            ?predicate a rdf:Property ;
                        ?space ?type .
        }""")

        def check_node_space(node, predicate, space, errmsg):
            """Check that a node conforms to it's allowable space of types.

            e.g. is a subject (node) the domain (space) of this property
            and is the object (node) the range of of this property.
            """
            resource_error = "Expected resource for {0} in range {1}"
            type_error = "Type of {0} was {1} not {2}"
            # check domain
            seen = set()
            errors = []
            for i, r in enumerate(self.model.query(property_query,
                                      initBindings={
                                          'predicate': predicate,
                                          'space': space})):
                # Make sure we have a resource if we're expecting one
                expected_type = r['type']

                if isinstance(node, Literal):
                    if expected_type == RDFS['Literal']:
                        return []
                    elif node.datatype == expected_type:
                        return []
                    else:
                        # not currently handling type hierarchy.
                        # a integer could pass a range of decimal for instance.
                        errors.append(
                            "Type error: {} was type {}, expected {}".format(
                                str(node),
                                str(node.datatype),
                                str(expected_type)))
                elif expected_type == RDFS['Resource']:
                    if isinstance(node, Literal):
                        errors.append(resource_error.format(str(node), space))
                    else:
                        return []
                else:
                    check = (node, RDF['type'], expected_type)
                    if check not in self.model:
                        errors.append(errmsg + str(node) + ' was not a ' + str(expected_type))
                    else:
                        return []

            return errors
        ### End nested function

        wrong_domain_type = "Domain of {0} was not in:"
        wrong_range_type = "Range of {0} was not in:"

        count = 0
        schema = ConjunctiveGraph(identifier=SCHEMAS_URL)
        for subject, predicate, obj, context in self.model.quads():
            stmt = (subject, predicate, obj)

            if context == schema:
                continue
            # check domain
            for error in check_node_space(subject, predicate, RDFS.domain,
                                          wrong_domain_type.format(str(stmt))):
                yield error
            # check range
            for error in check_node_space(obj, predicate, RDFS.range,
                                          wrong_range_type.format(str(stmt))):
                yield error
