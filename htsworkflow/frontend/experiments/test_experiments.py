import re
from lxml.html import fromstring
try:
    import json
except ImportError, e:
    import simplejson as json
import os
import shutil
import sys
import tempfile
from urlparse import urljoin

from django.conf import settings
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from htsworkflow.frontend.experiments import models
from htsworkflow.frontend.experiments import experiments
from htsworkflow.frontend.auth import apidata
from htsworkflow.util.ethelp import validate_xhtml

from htsworkflow.pipelines.test.simulate_runfolder import TESTDATA_DIR

LANE_SET = range(1,9)

NSMAP = {'libns':'http://jumpgate.caltech.edu/wiki/LibraryOntology#'}

class ClusterStationTestCases(TestCase):
    fixtures = ['test_flowcells.json']

    def test_default(self):
        c = models.ClusterStation.default()
        self.assertEqual(c.id, 2)

        c.isdefault = False
        c.save()

        total = models.ClusterStation.objects.filter(isdefault=True).count()
        self.assertEqual(total, 0)

        other_default = models.ClusterStation.default()
        self.assertEqual(other_default.id, 3)


    def test_update_default(self):
        old_default = models.ClusterStation.default()

        c = models.ClusterStation.objects.get(pk=3)
        c.isdefault = True
        c.save()

        new_default = models.ClusterStation.default()

        self.assertNotEqual(old_default, new_default)
        self.assertEqual(new_default, c)

        total = models.ClusterStation.objects.filter(isdefault=True).count()
        self.assertEqual(total, 1)

    def test_update_other(self):
        old_default = models.ClusterStation.default()
        total = models.ClusterStation.objects.filter(isdefault=True).count()
        self.assertEqual(total, 1)

        c = models.ClusterStation.objects.get(pk=1)
        c.name = "Primary Key 1"
        c.save()

        total = models.ClusterStation.objects.filter(isdefault=True).count()
        self.assertEqual(total, 1)

        new_default = models.ClusterStation.default()
        self.assertEqual(old_default, new_default)


class SequencerTestCases(TestCase):
    fixtures = ['test_flowcells.json']

    def test_default(self):
        # starting with no default
        s = models.Sequencer.default()
        self.assertEqual(s.id, 2)

        total = models.Sequencer.objects.filter(isdefault=True).count()
        self.assertEqual(total, 1)

        s.isdefault = False
        s.save()

        total = models.Sequencer.objects.filter(isdefault=True).count()
        self.assertEqual(total, 0)

        other_default = models.Sequencer.default()
        self.assertEqual(other_default.id, 7)

    def test_update_default(self):
        old_default = models.Sequencer.default()

        s = models.Sequencer.objects.get(pk=1)
        s.isdefault = True
        s.save()

        new_default = models.Sequencer.default()

        self.assertNotEqual(old_default, new_default)
        self.assertEqual(new_default, s)

        total = models.Sequencer.objects.filter(isdefault=True).count()
        self.assertEqual(total, 1)


    def test_update_other(self):
        old_default = models.Sequencer.default()
        total = models.Sequencer.objects.filter(isdefault=True).count()
        self.assertEqual(total, 1)

        s = models.Sequencer.objects.get(pk=1)
        s.name = "Primary Key 1"
        s.save()

        total = models.Sequencer.objects.filter(isdefault=True).count()
        self.assertEqual(total, 1)

        new_default = models.Sequencer.default()
        self.assertEqual(old_default, new_default)


class ExperimentsTestCases(TestCase):
    fixtures = ['test_flowcells.json',
                ]

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix='htsw-test-experiments-')
        settings.RESULT_HOME_DIR = self.tempdir

        self.fc1_id = 'FC12150'
        self.fc1_root = os.path.join(self.tempdir, self.fc1_id)
        os.mkdir(self.fc1_root)
        self.fc1_dir = os.path.join(self.fc1_root, 'C1-37')
        os.mkdir(self.fc1_dir)
        runxml = 'run_FC12150_2007-09-27.xml'
        shutil.copy(os.path.join(TESTDATA_DIR, runxml),
                    os.path.join(self.fc1_dir, runxml))
        for i in range(1,9):
            shutil.copy(
                os.path.join(TESTDATA_DIR,
                             'woldlab_070829_USI-EAS44_0017_FC11055_1.srf'),
                os.path.join(self.fc1_dir,
                             'woldlab_070829_SERIAL_FC12150_%d.srf' %(i,))
                )

        self.fc2_dir = os.path.join(self.tempdir, '42JTNAAXX')
        os.mkdir(self.fc2_dir)
        os.mkdir(os.path.join(self.fc2_dir, 'C1-25'))
        os.mkdir(os.path.join(self.fc2_dir, 'C1-37'))
        os.mkdir(os.path.join(self.fc2_dir, 'C1-37', 'Plots'))

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_flowcell_information(self):
        """
        Check the code that packs the django objects into simple types.
        """
        for fc_id in [u'FC12150', u"42JTNAAXX", "42JU1AAXX"]:
            fc_dict = experiments.flowcell_information(fc_id)
            fc_django = models.FlowCell.objects.get(flowcell_id=fc_id)
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
            fc_json = json.loads(response.content)
            self.assertEqual(fc_json['flowcell_id'], fc_id)
            self.assertEqual(fc_json['sequencer'], fc_django.sequencer.name)
            self.assertEqual(fc_json['read_length'], fc_django.read_length)
            self.assertEqual(fc_json['notes'], fc_django.notes)
            self.assertEqual(fc_json['cluster_station'], fc_django.cluster_station.name)


            for lane in fc_django.lane_set.all():
                lane_contents = fc_json['lane_set'][unicode(lane.lane_number)]
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
        response = self.client.get(u'/experiments/config/FC12150/json')
        self.assertEqual(response.status_code, 403)

    def test_library_id(self):
        """
        Library IDs should be flexible, so make sure we can retrive a non-numeric ID
        """
        response = self.client.get('/experiments/config/FC12150/json', apidata)
        self.assertEqual(response.status_code, 200)
        flowcell = json.loads(response.content)

        lane_contents = flowcell['lane_set']['3']
        lane_library = lane_contents[0]
        self.assertEqual(lane_library['library_id'], 'SL039')

        response = self.client.get('/samples/library/SL039/json', apidata)
        self.assertEqual(response.status_code, 200)
        library_sl039 = json.loads(response.content)

        self.assertEqual(library_sl039['library_id'], 'SL039')

    def test_raw_id_field(self):
        """
        Test ticket:147

        Library's have IDs, libraries also have primary keys,
        we eventually had enough libraries that the drop down combo box was too
        hard to filter through, unfortnately we want a field that uses our library
        id and not the internal primary key, and raw_id_field uses primary keys.

        This tests to make sure that the value entered in the raw library id field matches
        the library id looked up.
        """
        expected_ids = [u'10981',u'11016',u'SL039',u'11060',
                        u'11061',u'11062',u'11063',u'11064']
        self.client.login(username='supertest', password='BJOKL5kAj6aFZ6A5')
        response = self.client.get('/admin/experiments/flowcell/153/')

        tree = fromstring(response.content)
        for i in range(0,8):
            xpath_expression = '//input[@id="id_lane_set-%d-library"]'
            input_field = tree.xpath(xpath_expression % (i,))[0]
            library_field = input_field.find('../strong')
            library_id, library_name = library_field.text.split(':')
            # strip leading '#' sign from name
            library_id = library_id[1:]
            self.assertEqual(library_id, expected_ids[i])
            self.assertEqual(input_field.attrib['value'], library_id)

    def test_library_to_flowcell_link(self):
        """
        Make sure the library page includes links to the flowcell pages.
        That work with flowcell IDs that have parenthetical comments.
        """
        self.client.login(username='supertest', password='BJOKL5kAj6aFZ6A5')
        response = self.client.get('/library/11070/')
        self.assertEqual(response.status_code, 200)
        status = validate_xhtml(response.content)
        if status is not None: self.assertTrue(status)

        tree = fromstring(response.content)
        flowcell_spans = tree.xpath('//span[@property="libns:flowcell_id"]',
                                    namespaces=NSMAP)
        self.assertEqual(flowcell_spans[0].text, '30012AAXX (failed)')
        failed_fc_span = flowcell_spans[0]
        failed_fc_a = failed_fc_span.getparent()
        # make sure some of our RDF made it.
        self.assertEqual(failed_fc_a.get('typeof'), 'libns:IlluminaFlowcell')
        self.assertEqual(failed_fc_a.get('href'), '/flowcell/30012AAXX/')
        fc_response = self.client.get(failed_fc_a.get('href'))
        self.assertEqual(fc_response.status_code, 200)
        status = validate_xhtml(response.content)
        if status is not None: self.assertTrue(status)

        fc_lane_response = self.client.get('/flowcell/30012AAXX/8/')
        self.assertEqual(fc_lane_response.status_code, 200)
        status = validate_xhtml(response.content)
        if status is not None: self.assertTrue(status)


    def test_pooled_multiplex_id(self):
        fc_dict = experiments.flowcell_information('42JU1AAXX')
        lane_contents = fc_dict['lane_set'][3]
        self.assertEqual(len(lane_contents), 2)
        lane_dict = multi_lane_to_dict(lane_contents)

        self.assertEqual(lane_dict['12044']['index_sequence'],
                         {u'1': u'ATCACG',
                          u'2': u'CGATGT',
                          u'3': u'TTAGGC'})
        self.assertEqual(lane_dict['11045']['index_sequence'],
                         {u'1': u'ATCACG'})



    def test_lanes_for(self):
        """
        Check the code that packs the django objects into simple types.
        """
        user = 'test'
        lanes = experiments.lanes_for(user)
        self.assertEqual(len(lanes), 5)

        response = self.client.get('/experiments/lanes_for/%s/json' % (user,), apidata)
        lanes_json = json.loads(response.content)
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
        user = 'supertest'
        lanes = experiments.lanes_for(user)
        self.assertEqual(len(lanes), 0)

        response = self.client.get('/experiments/lanes_for/%s/json' % (user,), apidata)
        lanes_json = json.loads(response.content)

    def test_lanes_for_no_user(self):
        """
        Do we get something meaningful back when its the wrong user
        """
        user = 'not a real user'
        self.assertRaises(ObjectDoesNotExist, experiments.lanes_for, user)

        response = self.client.get('/experiments/lanes_for/%s/json' % (user,), apidata)
        self.assertEqual(response.status_code, 404)


    def test_raw_data_dir(self):
        """Raw data path generator check"""
        flowcell_id = self.fc1_id
        raw_dir = os.path.join(settings.RESULT_HOME_DIR, flowcell_id)

        fc = models.FlowCell.objects.get(flowcell_id=flowcell_id)
        self.assertEqual(fc.get_raw_data_directory(), raw_dir)

        fc.flowcell_id = flowcell_id + " (failed)"
        self.assertEqual(fc.get_raw_data_directory(), raw_dir)


    def test_data_run_import(self):
        srf_file_type = models.FileType.objects.get(name='SRF')
        runxml_file_type = models.FileType.objects.get(name='run_xml')
        flowcell_id = self.fc1_id
        flowcell = models.FlowCell.objects.get(flowcell_id=flowcell_id)
        flowcell.update_data_runs()
        self.assertEqual(len(flowcell.datarun_set.all()), 1)

        run = flowcell.datarun_set.all()[0]
        result_files = run.datafile_set.all()
        result_dict = dict(((rf.relative_pathname, rf) for rf in result_files))

        srf4 = result_dict['FC12150/C1-37/woldlab_070829_SERIAL_FC12150_4.srf']
        self.assertEqual(srf4.file_type, srf_file_type)
        self.assertEqual(srf4.library_id, '11060')
        self.assertEqual(srf4.data_run.flowcell.flowcell_id, 'FC12150')
        self.assertEqual(
            srf4.data_run.flowcell.lane_set.get(lane_number=4).library_id,
            '11060')
        self.assertEqual(
            srf4.pathname,
            os.path.join(settings.RESULT_HOME_DIR, srf4.relative_pathname))

        lane_files = run.lane_files()
        self.assertEqual(lane_files[4]['srf'], srf4)

        runxml= result_dict['FC12150/C1-37/run_FC12150_2007-09-27.xml']
        self.assertEqual(runxml.file_type, runxml_file_type)
        self.assertEqual(runxml.library_id, None)

        import1 = len(models.DataRun.objects.filter(result_dir='FC12150/C1-37'))
        # what happens if we import twice?
        flowcell.import_data_run('FC12150/C1-37',
                                 'run_FC12150_2007-09-27.xml')
        self.assertEqual(
            len(models.DataRun.objects.filter(result_dir='FC12150/C1-37')),
            import1)

    def test_read_result_file(self):
        """make sure we can return a result file
        """
        flowcell_id = self.fc1_id
        flowcell = models.FlowCell.objects.get(flowcell_id=flowcell_id)
        flowcell.update_data_runs()

        #self.client.login(username='supertest', password='BJOKL5kAj6aFZ6A5')

        result_files = flowcell.datarun_set.all()[0].datafile_set.all()
        for f in result_files:
            url = '/experiments/file/%s' % ( f.random_key,)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            mimetype = f.file_type.mimetype
            if mimetype is None:
                mimetype = 'application/octet-stream'

            self.assertEqual(mimetype, response['content-type'])

    def test_flowcell_rdf(self):
        import RDF
        from htsworkflow.util.rdfhelp import get_model, \
             fromTypedNode, \
             load_string_into_model, \
             rdfNS, \
             libraryOntology, \
             dump_model

        model = get_model()

        expected = {'1': ['11034'],
                    '2': ['11036'],
                    '3': ['12044','11045'],
                    '4': ['11047','13044'],
                    '5': ['11055'],
                    '6': ['11067'],
                    '7': ['11069'],
                    '8': ['11070']}
        url = '/flowcell/42JU1AAXX/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        status = validate_xhtml(response.content)
        if status is not None: self.assertTrue(status)

        ns = urljoin('http://localhost', url)
        load_string_into_model(model, 'rdfa', response.content, ns=ns)
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
        query = RDF.SPARQLQuery(body)
        count = 0
        for r in query.execute(model):
            count += 1
            self.assertEqual(fromTypedNode(r['flowcell_id']), u'42JU1AAXX')
            lane_id = fromTypedNode(r['lane_id'])
            library_id = fromTypedNode(r['library_id'])
            self.assertTrue(library_id in expected[lane_id])
        self.assertEqual(count, 10)


class TestFileType(TestCase):
    def test_file_type_unicode(self):
        file_type_objects = models.FileType.objects
        name = 'QSEQ tarfile'
        file_type_object = file_type_objects.get(name=name)
        self.assertEqual(u"<FileType: QSEQ tarfile>",
                             unicode(file_type_object))

class TestFileType(TestCase):
    def test_find_file_type(self):
        file_type_objects = models.FileType.objects
        cases = [('woldlab_090921_HWUSI-EAS627_0009_42FC3AAXX_l7_r1.tar.bz2',
                  'QSEQ tarfile', 7, 1),
                 ('woldlab_091005_HWUSI-EAS627_0010_42JT2AAXX_1.srf',
                  'SRF', 1, None),
                 ('s_1_eland_extended.txt.bz2','ELAND Extended', 1, None),
                 ('s_7_eland_multi.txt.bz2', 'ELAND Multi', 7, None),
                 ('s_3_eland_result.txt.bz2','ELAND Result', 3, None),
                 ('s_1_export.txt.bz2','ELAND Export', 1, None),
                 ('s_1_percent_call.png', 'IVC Percent Call', 1, None),
                 ('s_2_percent_base.png', 'IVC Percent Base', 2, None),
                 ('s_3_percent_all.png', 'IVC Percent All', 3, None),
                 ('s_4_call.png', 'IVC Call', 4, None),
                 ('s_5_all.png', 'IVC All', 5, None),
                 ('Summary.htm', 'Summary.htm', None, None),
                 ('run_42JT2AAXX_2009-10-07.xml', 'run_xml', None, None),
         ]
        for filename, typename, lane, end in cases:
            ft = models.find_file_type_metadata_from_filename(filename)
            self.assertEqual(ft['file_type'],
                                 file_type_objects.get(name=typename))
            self.assertEqual(ft.get('lane', None), lane)
            self.assertEqual(ft.get('end', None), end)

    def test_assign_file_type_complex_path(self):
        file_type_objects = models.FileType.objects
        cases = [('/a/b/c/woldlab_090921_HWUSI-EAS627_0009_42FC3AAXX_l7_r1.tar.bz2',
                  'QSEQ tarfile', 7, 1),
                 ('foo/woldlab_091005_HWUSI-EAS627_0010_42JT2AAXX_1.srf',
                  'SRF', 1, None),
                 ('../s_1_eland_extended.txt.bz2','ELAND Extended', 1, None),
                 ('/bleem/s_7_eland_multi.txt.bz2', 'ELAND Multi', 7, None),
                 ('/qwer/s_3_eland_result.txt.bz2','ELAND Result', 3, None),
                 ('/ty///1/s_1_export.txt.bz2','ELAND Export', 1, None),
                 ('/help/s_1_percent_call.png', 'IVC Percent Call', 1, None),
                 ('/bored/s_2_percent_base.png', 'IVC Percent Base', 2, None),
                 ('/example1/s_3_percent_all.png', 'IVC Percent All', 3, None),
                 ('amonkey/s_4_call.png', 'IVC Call', 4, None),
                 ('fishie/s_5_all.png', 'IVC All', 5, None),
                 ('/random/Summary.htm', 'Summary.htm', None, None),
                 ('/notrandom/run_42JT2AAXX_2009-10-07.xml', 'run_xml', None, None),
         ]
        for filename, typename, lane, end in cases:
            result = models.find_file_type_metadata_from_filename(filename)
            self.assertEqual(result['file_type'],
                                 file_type_objects.get(name=typename))
            self.assertEqual(result.get('lane',None), lane)
            self.assertEqual(result.get('end', None), end)

class TestEmailNotify(TestCase):
    fixtures = ['test_flowcells.json']

    def test_started_email_not_logged_in(self):
        response = self.client.get('/experiments/started/153/')
        self.assertEqual(response.status_code, 302)

    def test_started_email_logged_in_user(self):
        self.client.login(username='test', password='BJOKL5kAj6aFZ6A5')
        response = self.client.get('/experiments/started/153/')
        self.assertEqual(response.status_code, 302)

    def test_started_email_logged_in_staff(self):
        self.client.login(username='admintest', password='BJOKL5kAj6aFZ6A5')
        response = self.client.get('/experiments/started/153/')
        self.assertEqual(response.status_code, 200)

    def test_started_email_send(self):
        self.client.login(username='admintest', password='BJOKL5kAj6aFZ6A5')
        response = self.client.get('/experiments/started/153/')
        self.assertEqual(response.status_code, 200)

        self.assertTrue('pk1@example.com' in response.content)
        self.assertTrue('Lane #8 : (11064) Paired ends 104' in response.content)

        response = self.client.get('/experiments/started/153/', {'send':'1','bcc':'on'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 4)
        bcc = set(settings.NOTIFICATION_BCC).copy()
        bcc.update(set(settings.MANAGERS))
        for m in mail.outbox:
            self.assertTrue(len(m.body) > 0)
            self.assertEqual(set(m.bcc), bcc)

    def test_email_navigation(self):
        """
        Can we navigate between the flowcell and email forms properly?
        """
        self.client.login(username='supertest', password='BJOKL5kAj6aFZ6A5')
        response = self.client.get('/experiments/started/153/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(re.search('Flowcell FC12150', response.content))
        # require that navigation back to the admin page exists
        self.assertTrue(re.search('<a href="/admin/experiments/flowcell/153/">[^<]+</a>', response.content))

def multi_lane_to_dict(lane):
    """Convert a list of lane entries into a dictionary indexed by library ID
    """
    return dict( ((x['library_id'],x) for x in lane) )

class TestSequencer(TestCase):
    fixtures = ['test_flowcells.json',
                ]

    def test_name_generation(self):
        seq = models.Sequencer()
        seq.name = "Seq1"
        seq.instrument_name = "HWI-SEQ1"
        seq.model = "Imaginary 5000"

        self.assertEqual(unicode(seq), "Seq1 (HWI-SEQ1)")

    def test_lookup(self):
        fc = models.FlowCell.objects.get(pk=153)
        self.assertEqual(fc.sequencer.model,
                             "Illumina Genome Analyzer IIx")
        self.assertEqual(fc.sequencer.instrument_name,
                             "ILLUMINA-EC5D15")
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
        self.assertEqual(seq[0].attrib['about'], '/sequencer/2')
        self.assertEqual(seq[0].attrib['typeof'], 'libns:Sequencer')

        name = seq[0].xpath('./span[@property="libns:sequencer_name"]')
        self.assertEqual(len(name), 1)
        self.assertEqual(name[0].text, 'Tardigrade')
        instrument = seq[0].xpath(
            './span[@property="libns:sequencer_instrument"]')
        self.assertEqual(len(instrument), 1)
        self.assertEqual(instrument[0].text, 'ILLUMINA-EC5D15')
        model = seq[0].xpath(
            './span[@property="libns:sequencer_model"]')
        self.assertEqual(len(model), 1)
        self.assertEqual(model[0].text, 'Illumina Genome Analyzer IIx')

    def test_flowcell_with_rdf_validation(self):
        from htsworkflow.util.rdfhelp import add_default_schemas, \
             dump_model, \
             get_model, \
             load_string_into_model
        from htsworkflow.util.rdfinfer import Infer

        model = get_model()
        add_default_schemas(model)
        inference = Infer(model)

        url ='/flowcell/FC12150/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        status = validate_xhtml(response.content)
        if status is not None: self.assertTrue(status)

        load_string_into_model(model, 'rdfa', response.content)

        errmsgs = list(inference.run_validation())
        self.assertEqual(len(errmsgs), 2)
        for errmsg in errmsgs:
            self.assertEqual(errmsg, 'Missing type for: http://localhost/')

    def test_lane_with_rdf_validation(self):
        from htsworkflow.util.rdfhelp import add_default_schemas, \
             dump_model, \
             get_model, \
             load_string_into_model
        from htsworkflow.util.rdfinfer import Infer

        model = get_model()
        add_default_schemas(model)
        inference = Infer(model)

        url = '/lane/1193'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        status = validate_xhtml(response.content)
        if status is not None: self.assertTrue(status)

        load_string_into_model(model, 'rdfa', response.content)

        errmsgs = list(inference.run_validation())
        self.assertEqual(len(errmsgs), 2)
        for errmsg in errmsgs:
            self.assertEqual(errmsg, 'Missing type for: http://localhost/')
