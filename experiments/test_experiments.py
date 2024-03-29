from __future__ import absolute_import, print_function, unicode_literals

import logging
import re
from lxml.html import fromstring
import json
import os
import shutil
import tempfile
from six.moves.urllib.parse import urljoin

from django.conf import settings
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.test import TestCase
from django.utils.encoding import smart_str, smart_bytes

from rdflib import ConjunctiveGraph, Graph
from rdflib.namespace import RDF

from .models import SequencingRun, Sequencer, FlowCell, FileType
from samples.models import HTSUser
from .experiments import flowcell_information, lanes_for
from .experiments_factory import FlowCellFactory, LaneFactory
from samples.samples_factory import AffiliationFactory, HTSUserFactory, \
    LibraryFactory, LibraryTypeFactory, MultiplexIndexFactory
from htsworkflow.auth import apidata
from htsworkflow.util.ethelp import validate_xhtml
from encoded_client.rdfhelp import add_default_schemas
from htsworkflow.util.rdfinfer import Infer

from htsworkflow.pipelines.test.simulate_runfolder import TESTDATA_DIR

LANE_SET = range(1, 9)

NSMAP = {'libns': 'http://jumpgate.caltech.edu/wiki/LibraryOntology#'}


class ExperimentsTestCases(TestCase):
    def setUp(self):
        # Generate at least one fleshed out example flowcell
        self.tempdir = tempfile.mkdtemp(prefix='htsw-test-experiments-')
        settings.RESULT_HOME_DIR = self.tempdir

        self.password = 'password'
        self.user_odd = HTSUserFactory(username='user-odd')
        self.user_odd.set_password(self.password)
        self.affiliation_odd = AffiliationFactory(name='affiliation-odd', users=[self.user_odd])
        self.user_even = HTSUserFactory(username='user-even')
        self.user_even.set_password(self.password)
        self.affiliation_even = AffiliationFactory(name='affiliation-even', users=[self.user_even])
        self.admin = HTSUserFactory.create(username='admin', is_staff=True, is_superuser=True)
        self.admin.set_password(self.password)
        self.admin.save()

        self.fc12150 = FlowCellFactory(flowcell_id='FC12150')
        self.fc1_id = 'FC12150'
        self.fc1_root = os.path.join(self.tempdir, self.fc1_id)
        os.mkdir(self.fc1_root)
        self.fc1_dir = os.path.join(self.fc1_root, 'C1-37')
        os.mkdir(self.fc1_dir)
        runxml = 'run_FC12150_2007-09-27.xml'
        shutil.copy(os.path.join(TESTDATA_DIR, runxml),
                    os.path.join(self.fc1_dir, runxml))
        for i in range(1, 9):
            affiliation = self.affiliation_odd if i % 2 == 1 else self.affiliation_even
            library = LibraryFactory(id="1215" + str(i))
            library.affiliations.add(affiliation)
            lane = LaneFactory(flowcell=self.fc12150, lane_number=i, library=library)
            shutil.copy(
                os.path.join(TESTDATA_DIR,
                             'woldlab_070829_USI-EAS44_0017_FC11055_1.srf'),
                os.path.join(self.fc1_dir,
                             'woldlab_070829_SERIAL_FC12150_%d.srf' %(i,))
                )
        self.fc12150.save()

        self.fc42jtn = FlowCellFactory(flowcell_id='42JTNAAXX')
        self.fc42jtn_lanes = []
        for i in range(1, 9):
            affiliation = self.affiliation_odd if i % 2 == 1 else self.affiliation_even
            library_type = LibraryTypeFactory(can_multiplex=True)
            multiplex_index = MultiplexIndexFactory(adapter_type=library_type)
            library = LibraryFactory(id="1300" + str(i),
                                     library_type=library_type,
                                     multiplex_id=multiplex_index.multiplex_id)
            library.affiliations.add(affiliation)
            lane = LaneFactory(flowcell=self.fc42jtn, lane_number=(i % 2) + 1, library=library)
            self.fc42jtn_lanes.append(lane)

        self.fc2_dir = os.path.join(self.tempdir, '42JTNAAXX')
        os.mkdir(self.fc2_dir)
        os.mkdir(os.path.join(self.fc2_dir, 'C1-25'))
        os.mkdir(os.path.join(self.fc2_dir, 'C1-37'))
        os.mkdir(os.path.join(self.fc2_dir, 'C1-37', 'Plots'))
        logging.disable(logging.WARNING)

    def tearDown(self):
        shutil.rmtree(self.tempdir)
        self.user_odd.delete()
        self.user_even.delete()
        self.admin.delete()
        logging.disable(logging.NOTSET)

    def test_flowcells_index_rdfa(self):
        model = ConjunctiveGraph()

        response = self.client.get(reverse('flowcell_index'))
        self.assertEqual(response.status_code, 200)
        model.parse(data=smart_str(response.content), format="rdfa", media_type="text/html")

        add_default_schemas(model)
        inference = Infer(model)
        errmsgs = list(inference.run_validation())
        self.assertEqual(len(errmsgs), 0, errmsgs)

        body =  """prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>

        select ?flowcell
        where {
           ?flowcell a libns:IlluminaFlowcell .
        }"""
        bindings = set(['flowcell'])
        count = 0
        for r in model.query(body):
            count += 1

        self.assertEqual(count, len(FlowCell.objects.all()))

        # the << >> xml entity characters aren't available
        # state = validate_xhtml(response.content)
        # if state is not None:
        #    self.assertTrue(state)

    def test_flowcell_information(self):
        """
        Check the code that packs the django objects into simple types.
        """
        fc12150 = self.fc12150
        fc42jtn = self.fc42jtn
        fc42ju1 = FlowCellFactory(flowcell_id='42JU1AAXX')

        for fc_id in ['FC12150', '42JTNAAXX', '42JU1AAXX']:
            fc_dict = flowcell_information(fc_id)
            fc_django = FlowCell.objects.get(flowcell_id=fc_id)
            self.assertEqual(fc_dict['flowcell_id'], fc_id)
            self.assertEqual(fc_django.flowcell_id, fc_id)
            self.assertEqual(fc_dict['sequencer'], fc_django.sequencer.name)
            self.assertEqual(fc_dict['read_length'], fc_django.read_length)
            self.assertEqual(fc_dict['notes'], fc_django.notes)
            self.assertEqual(fc_dict['cluster_station'], fc_django.cluster_station.name)

            for lane in fc_django.lane_set.all():
                lane_contents = fc_dict['lane_set'][lane.lane_number]
                lane_dict = multi_lane_to_dict(lane_contents)[lane.library_id]
                self.assertEqual(lane_dict['cluster_estimate'], lane.cluster_estimate)
                self.assertEqual(lane_dict['comment'], lane.comment)
                self.assertEqual(lane_dict['flowcell'], lane.flowcell.flowcell_id)
                self.assertEqual(lane_dict['lane_number'], lane.lane_number)
                self.assertEqual(lane_dict['library_name'], lane.library.library_name)
                self.assertEqual(lane_dict['library_id'], lane.library.id)
                self.assertAlmostEqual(float(lane_dict['pM']), float(lane.pM))
                self.assertEqual(lane_dict['library_species'],
                                     lane.library.library_species.scientific_name)

            response = self.client.get('/experiments/config/%s/json' % (fc_id,), apidata)
            # strptime isoformat string = '%Y-%m-%dT%H:%M:%S'
            fc_json = json.loads(smart_str(response.content))['result']
            self.assertEqual(fc_json['flowcell_id'], fc_id)
            self.assertEqual(fc_json['sequencer'], fc_django.sequencer.name)
            self.assertEqual(fc_json['read_length'], fc_django.read_length)
            self.assertEqual(fc_json['notes'], fc_django.notes)
            self.assertEqual(fc_json['cluster_station'], fc_django.cluster_station.name)


            for lane in fc_django.lane_set.all():
                lane_contents = fc_json['lane_set'][str(lane.lane_number)]
                lane_dict = multi_lane_to_dict(lane_contents)[lane.library_id]

                self.assertEqual(lane_dict['cluster_estimate'], lane.cluster_estimate)
                self.assertEqual(lane_dict['comment'], lane.comment)
                self.assertEqual(lane_dict['flowcell'], lane.flowcell.flowcell_id)
                self.assertEqual(lane_dict['lane_number'], lane.lane_number)
                self.assertEqual(lane_dict['library_name'], lane.library.library_name)
                self.assertEqual(lane_dict['library_id'], lane.library.id)
                self.assertAlmostEqual(float(lane_dict['pM']), float(lane.pM))
                self.assertEqual(lane_dict['library_species'],
                                     lane.library.library_species.scientific_name)

    def test_invalid_flowcell(self):
        """
        Make sure we get a 404 if we request an invalid flowcell ID
        """
        response = self.client.get('/experiments/config/nottheone/json', apidata)
        self.assertEqual(response.status_code, 404)

    def test_no_key(self):
        """
        Require logging in to retrieve meta data
        """
        response = self.client.get('/experiments/config/FC12150/json')
        self.assertEqual(response.status_code, 403)

    def test_library_id(self):
        """make sure we can retrive a non-numeric library ID
        """
        response = self.client.get('/experiments/config/FC12150/json', apidata)
        self.assertEqual(response.status_code, 200)
        flowcell = json.loads(smart_str(response.content))['result']

        # library id is 12150 + lane number (1-8), so 12153
        lane_contents = flowcell['lane_set']['3']
        lane_library = lane_contents[0]
        self.assertEqual(lane_library['library_id'], '12153')

        response = self.client.get(reverse("library_json", args=("12153",)), apidata)
        self.assertEqual(response.status_code, 200)
        library_12153 = json.loads(smart_str(response.content))['result']

        self.assertEqual(library_12153['library_id'], '12153')

    def test_raw_id_field(self):
        """Test ticket:147

        Library's have IDs, libraries also have primary keys,
        we eventually had enough libraries that the drop down combo
        box was too hard to filter through, unfortnately we want a
        field that uses our library id and not the internal
        primary key, and raw_id_field uses primary keys.

        This tests to make sure that the value entered in the raw
        library id field matches the library id looked up.

        """
        expected_ids = ['1215{}'.format(i) for i in range(8, 0, -1)]
        self.assertTrue(self.client.login(username=self.admin.username, password=self.password))
        admin_url = reverse("admin:experiments_flowcell_change",
                            args=(self.fc12150.id,))
        response = self.client.get(admin_url, follow=True)
        self.assertEqual(response.status_code, 200)

        tree = fromstring(response.content)
        for i in range(0, 8):
            # this code to get to the block with the library id is a bit ugly
            # we find the input and then look a couple of tree elements after to find it.
            # I wonder if there's a way to get a class id or something on the
            # enclosing tag.
            xpath_expression = '//input[@id="id_lane_set-%d-library"]'
            input_field = tree.xpath(xpath_expression % (i,))[0]
            a_lookup = input_field.getnext()
            library_element = a_lookup.getnext()
            library_field = str(library_element.xpath('string(.)')).strip()
            library_id, library_name = library_field.split(':')
            # strip leading '#' sign from name
            library_id = library_id[1:]
            self.assertEqual(library_id, expected_ids[i])
            self.assertEqual(input_field.attrib['value'], library_id)

    def test_library_to_flowcell_link(self):
        """
        Make sure the library page includes links to the flowcell pages.
        That work with flowcell IDs that have parenthetical comments.
        """
        self.assertTrue(self.client.login(username=self.admin.username, password=self.password))
        response = self.client.get('/library/12151/')
        self.assertEqual(response.status_code, 200)
        status = validate_xhtml(response.content)
        if status is not None:
            self.assertTrue(status)

        tree = fromstring(response.content)
        flowcell_spans = tree.xpath('//span[@property="libns:flowcell_id"]',
                                    namespaces=NSMAP)
        self.assertEqual(flowcell_spans[1].text, 'FC12150')
        failed_fc_span = flowcell_spans[1]
        failed_fc_a = failed_fc_span.getparent()
        # make sure some of our RDF made it.
        self.assertEqual(failed_fc_a.get('typeof'), 'libns:IlluminaFlowcell')
        self.assertEqual(failed_fc_a.get('href'), '/flowcell/FC12150/')
        fc_response = self.client.get(failed_fc_a.get('href'))
        self.assertEqual(fc_response.status_code, 200)
        status = validate_xhtml(response.content)
        if status is not None: self.assertTrue(status)

        fc_lane_response = self.client.get('/flowcell/FC12150/8/')
        self.assertEqual(fc_lane_response.status_code, 200)
        status = validate_xhtml(response.content)
        if status is not None: self.assertTrue(status)

    def test_pooled_multiplex_id(self):
        fc_dict = flowcell_information(self.fc42jtn.flowcell_id)

        lane_contents = fc_dict['lane_set'][2]
        self.assertEqual(len(lane_contents), len(self.fc42jtn_lanes) / 2)
        lane_dict = multi_lane_to_dict(lane_contents)

        self.assertTrue(self.fc42jtn_lanes[0].library.multiplex_id in \
                        lane_dict['13001']['index_sequence'])
        self.assertTrue(self.fc42jtn_lanes[2].library.multiplex_id in \
                        lane_dict['13003']['index_sequence'])


    def test_lanes_for_view_user_odd(self):
        """Make sure lanes_for HTML UI works.
        """
        user = self.user_odd.username
        lanes = lanes_for(user)
        self.assertEqual(len(lanes), 8)

        response = self.client.get(
            reverse('lanes_for', kwargs={'username': user}))
        self.assertEqual(response.status_code, 200)
        tree = fromstring(response.content)
        lane_trs = tree.xpath('//div[@id="changelist"]/table/tbody/tr')
        self.assertEqual(len(lane_trs), len(lanes))
        # lanes is in db order
        # lane_trs is in newest to oldest order
        for lane_tr, lane_db in zip(lane_trs, lanes):
            library_id = lane_tr.xpath('td[6]/a')[0].text
            self.assertEqual(library_id, lane_db['library'])

    def test_lanes_for_view_invalid_user(self):
        """Make sure we don't find anything with an invalid user
        """
        response = self.client.get(
            reverse('lanes_for', kwargs={'username': 'doesntexist'}))
        self.assertEqual(response.status_code, 404)

    def test_lanes_for_json(self):
        """
        Check the code that packs the django objects into simple types.
        """
        user = self.user_odd.username
        lanes = lanes_for(user)
        self.assertEqual(len(lanes), 8)

        response = self.client.get('/experiments/lanes_for/%s/json' % (user,), apidata)
        lanes_json = json.loads(smart_str(response.content))['result']
        self.assertEqual(len(lanes), len(lanes_json))
        for i in range(len(lanes)):
            self.assertEqual(lanes[i]['comment'], lanes_json[i]['comment'])
            self.assertEqual(lanes[i]['lane_number'], lanes_json[i]['lane_number'])
            self.assertEqual(lanes[i]['flowcell'], lanes_json[i]['flowcell'])
            self.assertEqual(lanes[i]['run_date'], lanes_json[i]['run_date'])

    def test_lanes_for_no_lanes(self):
        """
        Do we get something meaningful back when the user isn't attached to anything?
        """
        user = HTSUserFactory.create(username='supertest')
        lanes = lanes_for(user.username)
        self.assertEqual(len(lanes), 0)

        response = self.client.get('/experiments/lanes_for/%s/json' % (user.username,), apidata)
        self.assertEqual(response.status_code, 200)
        result = json.loads(smart_str(response.content))
        self.assertEqual(result['result'], [])

    def test_lanes_for_no_user(self):
        """
        Do we get something meaningful back when its the wrong user
        """
        user = 'not a real user'
        self.assertRaises(ObjectDoesNotExist, lanes_for, user)

        response = self.client.get('/experiments/lanes_for/%s/json' % (user,), apidata)
        self.assertEqual(response.status_code, 404)

    def test_raw_data_dir(self):
        """Raw data path generator check"""
        flowcell_id = self.fc1_id
        raw_dir = os.path.join(settings.RESULT_HOME_DIR, flowcell_id)

        fc = FlowCell.objects.get(flowcell_id=flowcell_id)
        self.assertEqual(fc.get_raw_data_directory(), raw_dir)

        fc.flowcell_id = flowcell_id + " (failed)"
        self.assertEqual(fc.get_raw_data_directory(), raw_dir)

    def test_sequencing_run_import(self):
        srf_file_type = FileType.objects.get(name='SRF')
        runxml_file_type = FileType.objects.get(name='run_xml')
        flowcell_id = self.fc1_id
        flowcell = FlowCell.objects.get(flowcell_id=flowcell_id)
        flowcell.update_sequencing_runs()
        self.assertEqual(len(flowcell.sequencingrun_set.all()), 1)

        run = flowcell.sequencingrun_set.all()[0]
        result_files = run.datafile_set.all()
        result_dict = dict(((rf.relative_pathname, rf) for rf in result_files))

        srf4 = result_dict['FC12150/C1-37/woldlab_070829_SERIAL_FC12150_4.srf']
        self.assertEqual(srf4.file_type, srf_file_type)
        self.assertEqual(srf4.library_id, '12154')
        self.assertEqual(srf4.sequencing_run.flowcell.flowcell_id, 'FC12150')
        self.assertEqual(
            srf4.sequencing_run.flowcell.lane_set.get(lane_number=4).library_id,
            '12154')
        self.assertEqual(
            srf4.pathname,
            os.path.join(settings.RESULT_HOME_DIR, srf4.relative_pathname))

        lane_files = run.lane_files()
        self.assertEqual(lane_files[4]['srf'], srf4)

        runxml= result_dict['FC12150/C1-37/run_FC12150_2007-09-27.xml']
        self.assertEqual(runxml.file_type, runxml_file_type)
        self.assertEqual(runxml.library_id, None)

        import1 = len(SequencingRun.objects.filter(result_dir='FC12150/C1-37'))
        # what happens if we import twice?
        flowcell.import_sequencing_run('FC12150/C1-37',
                                       'run_FC12150_2007-09-27.xml')
        self.assertEqual(
            len(SequencingRun.objects.filter(result_dir='FC12150/C1-37')),
            import1)

    def test_read_result_file(self):
        """make sure we can return a result file
        """
        flowcell_id = self.fc1_id
        flowcell = FlowCell.objects.get(flowcell_id=flowcell_id)
        flowcell.update_sequencing_runs()

        result_files = flowcell.sequencingrun_set.all()[0].datafile_set.all()
        for f in result_files:
            url = reverse("read_result_file", args=(f.random_key,))
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            mimetype = f.file_type.mimetype
            if mimetype is None:
                mimetype = 'application/octet-stream'

            self.assertEqual(mimetype, response['content-type'])

    def test_flowcell_rdf(self):
        model = Graph()

        expected = {'1': ['12151'],
                    '2': ['12152'],
                    '3': ['12153'],
                    '4': ['12154'],
                    '5': ['12155'],
                    '6': ['12156'],
                    '7': ['12157'],
                    '8': ['12158']}
        lane_1 = self.fc12150.lane_set.get(lane_number='1')
        lane_1.status = 0
        lane_1.save()
        url = reverse('flowcell_detail', args=(self.fc12150.flowcell_id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        status = validate_xhtml(response.content)
        if status is not None: self.assertTrue(status)

        ns = urljoin('http://localhost', url)
        model.parse(data=smart_str(response.content), format="rdfa", media_type="text/html", publicID=ns)

        # find good lanes
        body = """prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>

        select ?flowcell ?flowcell_id ?lane_id ?library_id
        where {
          ?flowcell a libns:IlluminaFlowcell ;
                    libns:flowcell_id ?flowcell_id ;
                    libns:has_lane ?lane .
          ?lane libns:lane_number ?lane_id ;
                libns:library ?library .
          ?library libns:library_id ?library_id .
        }"""
        count = 0
        for r in model.query(body):
            count += 1
            self.assertEqual(r['flowcell_id'].toPython(), 'FC12150')
            lane_id = r['lane_id'].toPython()
            library_id = r['library_id'].toPython()
            self.assertTrue(library_id in expected[lane_id])
        self.assertEqual(count, 7)

        # find bad lanes
        body = """prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        prefix libns: <http://jumpgate.caltech.edu/wiki/LibraryOntology#>

        select ?flowcell ?flowcell_id ?lane_id ?library_id
        where {
          ?flowcell a libns:IlluminaFlowcell ;
                    libns:flowcell_id ?flowcell_id ;
                    libns:has_failed_lane ?lane .
          ?lane libns:lane_number ?lane_id ;
                libns:library ?library .
          ?library libns:library_id ?library_id .
        }"""
        count = 0
        for r in model.query(body):
            count += 1
            self.assertEqual(r['flowcell_id'].toPython(), 'FC12150')
            lane_id = r['lane_id'].toPython()
            library_id = r['library_id'].toPython()
            self.assertTrue(library_id in expected[lane_id])
        self.assertEqual(count, 1)


class TestEmailNotify(TestCase):
    def setUp(self):
        self.password = 'foo27'
        self.user = HTSUserFactory.create(username='test')
        self.user.set_password(self.password)
        self.user.save()
        self.admin = HTSUserFactory.create(username='admintest', is_staff=True)
        self.admin.set_password(self.password)
        self.admin.save()
        self.superuser = HTSUserFactory.create(username='supertest', is_staff=True, is_superuser=True)
        self.superuser.set_password(self.password)
        self.superuser.save()

        self.library = LibraryFactory.create()
        self.affiliation = AffiliationFactory()
        self.affiliation.users.add(self.user)
        self.library.affiliations.add(self.affiliation)
        self.fc = FlowCellFactory.create()
        self.lane = LaneFactory(flowcell=self.fc, lane_number=1, library=self.library)

        self.url = reverse("started_email", args=(self.fc.id,))

    def tearDown(self):
        # with django 1.10 running against postgresql I had to delete these
        # test objects or else I get a constraint error
        self.affiliation.delete()
        self.user.delete()
        self.admin.delete()
        self.superuser.delete()

    def test_started_email_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_started_email_logged_in_user(self):
        self.assertTrue(self.client.login(username=self.user.username, password=self.password))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_started_email_logged_in_staff(self):
        self.assertTrue(self.admin.is_staff)
        admin = HTSUser.objects.get(username=self.admin.username)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.check_password(self.password))
        self.assertTrue(self.client.login(username=self.admin.username, password=self.password))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_started_email_send(self):
        self.assertTrue(self.client.login(username=self.admin.username, password=self.password))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(self.affiliation.email in smart_str(response.content))
        self.assertTrue(self.library.library_name in smart_str(response.content))

        response = self.client.get(self.url, {'send': '1', 'bcc': 'on'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)
        bcc = set(settings.NOTIFICATION_BCC).copy()
        bcc.update(set(settings.MANAGERS))
        for m in mail.outbox:
            self.assertTrue(len(m.body) > 0)
            self.assertEqual(set(m.bcc), bcc)

    def test_email_navigation(self):
        """
        Can we navigate between the flowcell and email forms properly?
        """
        admin_url = reverse("admin:experiments_flowcell_change",
                            args=(self.fc.id,))
        self.client.login(username=self.admin.username, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(re.search(self.fc.flowcell_id, smart_str(response.content)))
        # require that navigation back to the admin page exists
        admin_a_tag = '<a href="{}">[^<]+</a>'.format(admin_url)
        self.assertTrue(re.search(admin_a_tag, smart_str(response.content)))

def multi_lane_to_dict(lane):
    """Convert a list of lane entries into a dictionary indexed by library ID
    """
    return dict( ((x['library_id'],x) for x in lane) )

class TestSequencer(TestCase):
    def setUp(self):
        self.fc12150 = FlowCellFactory(flowcell_id='FC12150')
        self.library = LibraryFactory(id="12150")
        self.lane = LaneFactory(flowcell=self.fc12150, lane_number=1, library=self.library)

    def test_name_generation(self):
        seq = Sequencer()
        seq.name = "Seq1"
        seq.instrument_name = "HWI-SEQ1"
        seq.model = "Imaginary 5000"

        self.assertEqual(str(seq), "Seq1 (HWI-SEQ1)")

    def test_lookup(self):
        fc = self.fc12150
        self.assertEqual(fc.sequencer.model, 'HiSeq 1')
        self.assertTrue(fc.sequencer.instrument_name.startswith('instrument name')),
        # well actually we let the browser tack on the host name
        url = fc.get_absolute_url()
        self.assertEqual(url, '/flowcell/FC12150/')

    def test_rdf(self):
        response = self.client.get('/flowcell/FC12150/', apidata)
        tree = fromstring(response.content)
        seq_by = tree.xpath('//div[@rel="libns:sequenced_by"]',
                            namespaces=NSMAP)
        self.assertEqual(len(seq_by), 1)
        self.assertEqual(seq_by[0].attrib['rel'], 'libns:sequenced_by')
        seq = seq_by[0].getchildren()
        self.assertEqual(len(seq), 1)
        sequencer = '/sequencer/' + str(self.fc12150.sequencer.id)
        self.assertEqual(seq[0].attrib['about'], sequencer)
        self.assertEqual(seq[0].attrib['typeof'], 'libns:Sequencer')

        name = seq[0].xpath('./span[@property="libns:sequencer_name"]')
        self.assertEqual(len(name), 1)
        self.assertTrue(name[0].text.startswith('sequencer '))
        instrument = seq[0].xpath(
            './span[@property="libns:sequencer_instrument"]')
        self.assertEqual(len(instrument), 1)
        self.assertTrue(instrument[0].text.startswith('instrument name'))
        model = seq[0].xpath(
            './span[@property="libns:sequencer_model"]')
        self.assertEqual(len(model), 1)
        self.assertEqual(model[0].text, 'HiSeq 1')

    def test_flowcell_with_rdf_validation(self):

        model = ConjunctiveGraph()
        add_default_schemas(model)
        inference = Infer(model)

        url = reverse("flowcell_detail", args=('FC12150',))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        status = validate_xhtml(response.content)
        if status is not None:
            self.assertTrue(status)

        model.parse(data=smart_str(response.content), format="rdfa", media_type="text/html")

        errmsgs = list(inference.run_validation())
        self.assertEqual(len(errmsgs), 0)

    def test_lane_with_rdf_validation(self):
        model = ConjunctiveGraph()
        add_default_schemas(model)
        inference = Infer(model)

        url = reverse("flowcell_lane_detail", args=(self.lane.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        status = validate_xhtml(smart_bytes(response.content))
        if status is not None:
            self.assertTrue(status)

        model.parse(data=smart_str(response.content), format="rdfa", media_type="text/html")
        errmsgs = list(inference.run_validation())
        self.assertEqual(len(errmsgs), 0)

def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    for testcase in [ExerimentsTestCases,
                     TestEmailNotify,
                     TestSequencer]:
        suite.addTests(defaultTestLoader.loadTestsFromTestCase(testcase))
    return suite

if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
