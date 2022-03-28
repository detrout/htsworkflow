from __future__ import absolute_import, print_function

import datetime
import json
import logging
from unittest import skipUnless

from django.core.exceptions import ValidationError
from django.urls import reverse
from django.test import TestCase, RequestFactory
from django.utils.encoding import smart_text, smart_str, smart_bytes

from rdflib import ConjunctiveGraph, Graph, URIRef

from lxml import html

from .models import Affiliation, ExperimentType, Species, Library
from .views import library_dict
from .samples_factory import (
    AffiliationFactory,
    HTSUserFactory,
    LibraryAccessionFactory,
    LibraryFactory,
    SpeciesFactory,
)
from experiments.experiments_factory import LaneFactory, FlowCellFactory

from htsworkflow.auth import apidata
from htsworkflow.util.conversion import str_or_none
from htsworkflow.util.ethelp import validate_xhtml

from encoded_client.rdfhelp import add_default_schemas
from encoded_client.rdfns import libraryOntology
from htsworkflow.util.rdfinfer import Infer


class LibraryAccessionTestCase(TestCase):
    def test_validator(self):
        library = LibraryFactory()
        acc = LibraryAccessionFactory(library_id=library.id)
        acc.clean_fields()
        accession = acc.accession
        # test a variety of escape characters one at a time
        for c in "<>'\"&;":
            acc.accession = accession + c
            self.assertRaises(ValidationError, acc.clean_fields)

    def test_library_save_hook(self):
        library = LibraryFactory()
        acc = LibraryAccessionFactory(library_id=library.id)

        self.assertEqual(acc.url[: len(acc.agency.homepage)], acc.agency.homepage)
        self.assertEqual(
            acc.url[len(acc.agency.homepage) :], "/library/" + acc.accession
        )

    def test_have_accession(self):
        library = LibraryFactory()
        acc = LibraryAccessionFactory(library_id=library.id)
        lib_response = self.client.get(library.get_absolute_url())
        lib_content = smart_text(lib_response.content)

        model = Graph()
        model.parse(data=lib_content, format="rdfa", media_type="text/html")

        body = """prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>

        select ?library ?accession
        where {
           ?library libns:accession ?accession
        }"""
        accessions = []
        for row in model.query(body):
            accessions.append(str(row["accession"]))
        self.assertEqual(len(accessions), 1)
        self.assertEqual(accessions[0], acc.url)


class LibraryTestCase(TestCase):
    def testOrganism(self):
        human = SpeciesFactory(common_name="human")
        self.assertEqual(human.common_name, "human")
        library = LibraryFactory(library_species=human)
        self.assertEqual(library.organism(), "human")

    def testAddingOneAffiliation(self):
        affiliation = AffiliationFactory.create(name="Alice")
        library = LibraryFactory()
        library.affiliations.add(affiliation)

        self.assertEqual(len(library.affiliations.all()), 1)
        self.assertEqual(library.affiliation(), "Alice (contact name)")

    def testMultipleAffiliations(self):
        alice = AffiliationFactory.create(name="Alice")
        bob = AffiliationFactory.create(name="Bob")

        library = LibraryFactory()
        library.affiliations.add(alice, bob)

        self.assertEqual(len(library.affiliations.all()), 2)
        self.assertEqual(
            library.affiliation(), "Alice (contact name), Bob (contact name)"
        )


class SampleWebTestCase(TestCase):
    """
    Test returning data from our database in rest like ways.
    (like returning json objects)
    """

    def setUp(self):
        logging.disable(logging.WARNING)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_library_dict(self):
        library = LibraryFactory.create()
        lib_dict = library_dict(library.id)
        url = reverse("library_json", args=(library.id,))
        lib_response = self.client.get(url, apidata)
        lib_json = json.loads(smart_text(lib_response.content))["result"]

        for d in [lib_dict, lib_json]:
            # amplified_from_sample is a link to the library table,
            # I want to use the "id" for the data lookups not
            # the embedded primary key.
            # It gets slightly confusing on how to implement sending the right id
            # since amplified_from_sample can be null
            # self.assertEqual(d['amplified_from_sample'], lib.amplified_from_sample)
            self.assertEqual(d["antibody_id"], library.antibody_id)
            self.assertEqual(d["cell_line_id"], library.cell_line_id)
            self.assertEqual(d["cell_line"], str_or_none(library.cell_line))
            self.assertEqual(d["experiment_type"], library.experiment_type.name)
            self.assertEqual(d["experiment_type_id"], library.experiment_type_id)
            self.assertEqual(d["gel_cut_size"], library.gel_cut_size)
            self.assertEqual(d["hidden"], library.hidden)
            self.assertEqual(d["id"], library.id)
            self.assertEqual(d["insert_size"], library.insert_size)
            self.assertEqual(d["library_name"], library.library_name)
            self.assertEqual(
                d["library_species"], library.library_species.scientific_name
            )
            self.assertEqual(d["library_species_id"], library.library_species_id)
            self.assertEqual(d["library_type_id"], library.library_type_id)
            self.assertTrue(d["library_type"].startswith("library type"))
            self.assertEqual(d["made_for"], library.made_for)
            self.assertEqual(d["made_by"], library.made_by)
            self.assertEqual(d["notes"], library.notes)
            self.assertEqual(d["replicate"], library.replicate)
            self.assertEqual(d["stopping_point"], library.stopping_point)
            self.assertEqual(d["successful_pM"], library.successful_pM)
            self.assertEqual(
                d["undiluted_concentration"], str(library.undiluted_concentration)
            )

    def test_invalid_library_json(self):
        """
        Make sure we get a 404 if we request an invalid library id
        """
        url = reverse("library_json", args=("nottheone",))
        response = self.client.get(url, apidata)
        self.assertEqual(response.status_code, 404)

    def test_invalid_library(self):
        url = reverse("library_detail", args=("nottheone",))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_library_no_key(self):
        """
        Make sure we get a 403 if we're not logged in
        """
        library = LibraryFactory.create()

        url = reverse("library_json", args=(library.id,))
        response = self.client.get(url, apidata)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_1_not_run(self):
        """Create library that was not run, make sure it shows up in non_run filter"""
        library = LibraryFactory.create()
        url = reverse("library_not_run")
        self.assertEqual(url, "/library/not_run/")
        response = self.client.get(url)
        self.assertTrue(library.id in smart_str(response.content))

        model = ConjunctiveGraph()
        model.parse(
            data=smart_text(response.content), format="rdfa", media_type="text/html"
        )
        body = """prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>

        select ?library ?library_id
        where {
           ?library a libns:Library ;
                    libns:library_id ?library_id .
        }"""
        results = []
        for r in model.query(body):
            results.append(r["library_id"])

        self.assertEqual(len(results), 1)

    def test_0_not_run(self):
        """Create a library that was run, so it won't show up with not_run filter"""
        lane = LaneFactory()
        library = lane.library
        url = reverse("library_not_run")
        response = self.client.get(url)

        model = ConjunctiveGraph()
        model.parse(
            data=smart_text(response.content), format="rdfa", media_type="text/html"
        )
        body = """prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>

        select ?library ?library_id
        where {
           ?library a libns:Library ;
                    libns:library_id ?library_id .
        }"""
        results = []
        for r in model.query(body):
            results.append(r["library_id"])

        self.assertEqual(len(results), 0)

    def test_library_rdf(self):
        library = LibraryFactory.create()

        model = ConjunctiveGraph()

        response = self.client.get(library.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        model.parse(
            data=smart_text(response.content), format="rdfa", media_type="text/html"
        )

        body = """prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>

        select ?library ?name ?library_id ?gel_cut ?made_by
        where {
           ?library a libns:Library ;
                    libns:name ?name ;
                    libns:library_id ?library_id ;
                    libns:gel_cut ?gel_cut ;
                    libns:made_by ?made_by
        }"""

        count = 0
        for r in model.query(body):
            self.assertEqual(r["library_id"].toPython(), library.id)
            self.assertEqual(r["name"].toPython(), library.library_name)
            self.assertEqual(r["gel_cut"].toPython(), library.gel_cut_size)
            self.assertEqual(r["made_by"].toPython(), library.made_by)
            count += 1

        # make sure there was actually data
        self.assertGreater(count, 0)

        state = validate_xhtml(smart_bytes(response.content))
        if state is not None:
            self.assertTrue(state)

        # validate a library page.
        add_default_schemas(model)
        inference = Infer(model)
        errmsgs = list(inference.run_validation())
        self.assertEqual(len(errmsgs), 0)

    def test_library_index_rdfa(self):
        model = ConjunctiveGraph()
        add_default_schemas(model)
        inference = Infer(model)

        response = self.client.get(reverse("library_index"))
        self.assertEqual(response.status_code, 200)
        model.parse(
            data=smart_text(response.content), format="rdfa", media_type="text/html"
        )

        errmsgs = list(inference.run_validation())
        self.assertEqual(len(errmsgs), 0)

        body = """prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>

        select ?library ?library_id ?name ?species ?species_name
        where {
           ?library a libns:Library .
           OPTIONAL { ?library libns:library_id ?library_id . }
           OPTIONAL { ?library libns:species ?species .
                      ?species libns:species_name ?species_name . }
           OPTIONAL { ?library libns:name ?name . }
        }"""
        bindings = set(["library", "library_id", "name", "species", "species_name"])
        count = 0
        for r in model.query(body):
            count += 1
            for name, value in r.items():
                self.assertTrue(name in bindings)
                self.assertTrue(value is not None)

        self.assertEqual(count, len(Library.objects.filter(hidden=False)))

        state = validate_xhtml(response.content)
        if state is not None:
            self.assertTrue(state)

    @skipUnless(
        hasattr(TestCase.client_class, "force_login"),
        "Django missing client.force_login",
    )
    def test_login(self):
        """Test login header on library page changes when the user logins"""
        user = HTSUserFactory(username="user")

        # not logged in
        response = self.client.get(reverse("library_index"))
        tree = html.fromstring(response.content)
        login_url = tree.xpath('//div[@id="user-tools"]/a')[0].attrib["href"]
        self.assertTrue(
            login_url.startswith(reverse("login")), "url={}".format(login_url)
        )

        # login
        self.client.force_login(user)

        # does the banner change?
        response = self.client.get(reverse("library_index"))
        tree = html.fromstring(response.content)
        logout_url = tree.xpath('//div[@id="user-tools"]/a')[-1].attrib["href"]
        self.assertTrue(logout_url.startswith(reverse("logout")))


# The django test runner flushes the database between test suites not cases,
# so to be more compatible with running via nose we flush the database tables
# of interest before creating our sample data.
def create_db(obj):
    obj.species_human = Species.objects.get(pk=8)
    obj.experiment_rna_seq = ExperimentType.objects.get(pk=4)
    obj.affiliation_alice = Affiliation.objects.get(pk=1)
    obj.affiliation_bob = Affiliation.objects.get(pk=2)

    Library.objects.all().delete()
    obj.library_10001 = Library(
        id="10001",
        library_name="C2C12 named poorly",
        library_species=obj.species_human,
        experiment_type=obj.experiment_rna_seq,
        creation_date=datetime.datetime.now(),
        made_for="scientist unit 2007",
        made_by="microfludics system 7321",
        stopping_point="2A",
        undiluted_concentration="5.01",
        hidden=False,
    )
    obj.library_10001.save()
    obj.library_10002 = Library(
        id="10002",
        library_name="Worm named poorly",
        library_species=obj.species_human,
        experiment_type=obj.experiment_rna_seq,
        creation_date=datetime.datetime.now(),
        made_for="scientist unit 2007",
        made_by="microfludics system 7321",
        stopping_point="2A",
        undiluted_concentration="5.01",
        hidden=False,
    )
    obj.library_10002.save()


class TestRDFaLibrary(TestCase):
    def setUp(self):
        self.request = RequestFactory()

    def test_parse_rdfa(self):
        model = Graph()

        bob = AffiliationFactory.create(name="Bob")

        lib_object = LibraryFactory()
        lib_object.affiliations.add(bob)
        fc = FlowCellFactory()
        lanes = []
        for i in range(1, 3):
            # mark even lanes as failed.
            lanes.append(
                LaneFactory(
                    flowcell=fc,
                    lane_number=i,
                    library=lib_object,
                    status=0 if i % 2 == 0 else None,
                )
            )
        url = reverse("library_detail", args=(lib_object.id,))
        ## request = self.request.get(url)
        ## lib_response = library(request)
        lib_response = self.client.get(url)
        lib_body = smart_str(lib_response.content)
        self.assertNotEqual(len(lib_body), 0)

        model.parse(
            data=lib_body,
            format="rdfa",
            media_type="text/html",
            publicID="http://localhost" + url,
        )

        # http://jumpgate.caltech.edu/wiki/LibraryOntology#affiliation>
        self.check_literal_object(model, ["Bob"], p=libraryOntology["affiliation"])
        self.check_literal_object(
            model, ["experiment type name"], p=libraryOntology["experiment_type"]
        )
        self.check_literal_object(model, [400], p=libraryOntology["gel_cut"])
        self.check_literal_object(
            model, ["microfluidics bot 7321"], p=libraryOntology["made_by"]
        )
        self.check_literal_object(
            model, [lib_object.library_name], p=libraryOntology["name"]
        )
        self.check_literal_object(
            model,
            [lib_object.library_species.scientific_name],
            p=libraryOntology["species_name"],
        )

        library_url = "http://localhost/library/{}/".format(lib_object.id)
        lane_url = "http://localhost/lane/{}"
        for uri, term, expected in [
            (library_url, libraryOntology["has_lane"], lane_url.format(lanes[0].id)),
            (
                library_url,
                libraryOntology["has_failed_lane"],
                lane_url.format(lanes[1].id),
            ),
        ]:
            triples = list(model.triples((URIRef(uri), term, None)))
            self.assertEqual(len(triples), 1)
            self.assertEqual(triples[0][2], URIRef(expected))

        for uri, expected in [
            (lane_url.format(lanes[0].id), ""),
            (lane_url.format(lanes[1].id), "Failed"),
        ]:
            triples = list(
                model.triples((URIRef(uri), libraryOntology["status"], None))
            )
            self.assertEqual(len(triples), 1)
            self.assertEqual(triples[0][2].toPython(), expected)

    def check_literal_object(self, model, values, s=None, p=None, o=None):
        statements = list(model.triples((s, p, o)))
        self.assertEqual(
            len(statements), len(values), "Couln't find %s %s %s" % (s, p, o)
        )
        for stmt in statements:
            obj = stmt[2]
            self.assertIn(obj.value, values)

    def check_uri_object(self, model, values, s=None, p=None, o=None):
        statements = list(model.triples((s, p, o)))
        self.assertEqual(
            len(statements), len(values), "Couln't find %s %s %s" % (s, p, o)
        )
        for stmt in statements:
            subject = stmt[0]
            self.assertIn(str(subject.value), values)


def suite():
    from unittest import TestSuite, defaultTestLoader

    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(LibraryAccessionTestCase))
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(LibraryTestCase))
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(SampleWebTestCase))
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestRDFaLibrary))
    return suite


if __name__ == "__main__":
    from unittest import main

    main(defaultTest="suite")
