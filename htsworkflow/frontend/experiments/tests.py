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

from django.conf import settings
from django.core import mail
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from htsworkflow.frontend.experiments import models
from htsworkflow.frontend.experiments import experiments
from htsworkflow.frontend.auth import apidata

from htsworkflow.pipelines.test.simulate_runfolder import TESTDATA_DIR

LANE_SET = range(1,9)

NSMAP = {'libns':'http://jumpgate.caltech.edu/wiki/LibraryOntology#'}

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
            self.failUnlessEqual(fc_dict['flowcell_id'], fc_id)
            self.failUnlessEqual(fc_django.flowcell_id, fc_id)
            self.failUnlessEqual(fc_dict['sequencer'], fc_django.sequencer.name)
            self.failUnlessEqual(fc_dict['read_length'], fc_django.read_length)
            self.failUnlessEqual(fc_dict['notes'], fc_django.notes)
            self.failUnlessEqual(fc_dict['cluster_station'], fc_django.cluster_station.name)

            for lane in fc_django.lane_set.all():
                lane_contents = fc_dict['lane_set'][lane.lane_number]
                lane_dict = multi_lane_to_dict(lane_contents)[lane.library_id]
                self.failUnlessEqual(lane_dict['cluster_estimate'], lane.cluster_estimate)
                self.failUnlessEqual(lane_dict['comment'], lane.comment)
                self.failUnlessEqual(lane_dict['flowcell'], lane.flowcell.flowcell_id)
                self.failUnlessEqual(lane_dict['lane_number'], lane.lane_number)
                self.failUnlessEqual(lane_dict['library_name'], lane.library.library_name)
                self.failUnlessEqual(lane_dict['library_id'], lane.library.id)
                self.failUnlessAlmostEqual(float(lane_dict['pM']), float(lane.pM))
                self.failUnlessEqual(lane_dict['library_species'],
                                     lane.library.library_species.scientific_name)

            response = self.client.get('/experiments/config/%s/json' % (fc_id,), apidata)
            # strptime isoformat string = '%Y-%m-%dT%H:%M:%S'
            fc_json = json.loads(response.content)
            self.failUnlessEqual(fc_json['flowcell_id'], fc_id)
            self.failUnlessEqual(fc_json['sequencer'], fc_django.sequencer.name)
            self.failUnlessEqual(fc_json['read_length'], fc_django.read_length)
            self.failUnlessEqual(fc_json['notes'], fc_django.notes)
            self.failUnlessEqual(fc_json['cluster_station'], fc_django.cluster_station.name)


            for lane in fc_django.lane_set.all():
                lane_contents = fc_json['lane_set'][unicode(lane.lane_number)]
                lane_dict = multi_lane_to_dict(lane_contents)[lane.library_id]

                self.failUnlessEqual(lane_dict['cluster_estimate'], lane.cluster_estimate)
                self.failUnlessEqual(lane_dict['comment'], lane.comment)
                self.failUnlessEqual(lane_dict['flowcell'], lane.flowcell.flowcell_id)
                self.failUnlessEqual(lane_dict['lane_number'], lane.lane_number)
                self.failUnlessEqual(lane_dict['library_name'], lane.library.library_name)
                self.failUnlessEqual(lane_dict['library_id'], lane.library.id)
                self.failUnlessAlmostEqual(float(lane_dict['pM']), float(lane.pM))
                self.failUnlessEqual(lane_dict['library_species'],
                                     lane.library.library_species.scientific_name)

    def test_invalid_flowcell(self):
        """
        Make sure we get a 404 if we request an invalid flowcell ID
        """
        response = self.client.get('/experiments/config/nottheone/json', apidata)
        self.failUnlessEqual(response.status_code, 404)

    def test_no_key(self):
        """
        Require logging in to retrieve meta data
        """
        response = self.client.get(u'/experiments/config/FC12150/json')
        self.failUnlessEqual(response.status_code, 403)

    def test_library_id(self):
        """
        Library IDs should be flexible, so make sure we can retrive a non-numeric ID
        """
        response = self.client.get('/experiments/config/FC12150/json', apidata)
        self.failUnlessEqual(response.status_code, 200)
        flowcell = json.loads(response.content)

        lane_contents = flowcell['lane_set']['3']
        lane_library = lane_contents[0]
        self.failUnlessEqual(lane_library['library_id'], 'SL039')

        response = self.client.get('/samples/library/SL039/json', apidata)
        self.failUnlessEqual(response.status_code, 200)
        library_sl039 = json.loads(response.content)

        self.failUnlessEqual(library_sl039['library_id'], 'SL039')

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
            self.failUnlessEqual(library_id, expected_ids[i])
            self.failUnlessEqual(input_field.attrib['value'], library_id)

    def test_library_to_flowcell_link(self):
        """
        Make sure the library page includes links to the flowcell pages.
        That work with flowcell IDs that have parenthetical comments.
        """
        self.client.login(username='supertest', password='BJOKL5kAj6aFZ6A5')
        response = self.client.get('/library/11070/')
        tree = fromstring(response.content)
        flowcell_spans = tree.xpath('//span[@property="libns:flowcell_id"]',
                                    namespaces=NSMAP)
        self.assertEqual(flowcell_spans[0].text, '30012AAXX (failed)')
        failed_fc_span = flowcell_spans[0]
        failed_fc_a = failed_fc_span.getparent()
        # make sure some of our RDF made it.
        self.failUnlessEqual(failed_fc_a.get('rel'), 'libns:flowcell')
        self.failUnlessEqual(failed_fc_a.get('href'), '/flowcell/30012AAXX/')
        fc_response = self.client.get(failed_fc_a.get('href'))
        self.failUnlessEqual(fc_response.status_code, 200)
        fc_lane_response = self.client.get('/flowcell/30012AAXX/8/')
        self.failUnlessEqual(fc_lane_response.status_code, 200)

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
        self.failUnlessEqual(len(lanes), 5)

        response = self.client.get('/experiments/lanes_for/%s/json' % (user,), apidata)
        lanes_json = json.loads(response.content)
        self.failUnlessEqual(len(lanes), len(lanes_json))
        for i in range(len(lanes)):
            self.failUnlessEqual(lanes[i]['comment'], lanes_json[i]['comment'])
            self.failUnlessEqual(lanes[i]['lane_number'], lanes_json[i]['lane_number'])
            self.failUnlessEqual(lanes[i]['flowcell'], lanes_json[i]['flowcell'])
            self.failUnlessEqual(lanes[i]['run_date'], lanes_json[i]['run_date'])

    def test_lanes_for_no_lanes(self):
        """
        Do we get something meaningful back when the user isn't attached to anything?
        """
        user = 'supertest'
        lanes = experiments.lanes_for(user)
        self.failUnlessEqual(len(lanes), 0)

        response = self.client.get('/experiments/lanes_for/%s/json' % (user,), apidata)
        lanes_json = json.loads(response.content)

    def test_lanes_for_no_user(self):
        """
        Do we get something meaningful back when its the wrong user
        """
        user = 'not a real user'
        self.failUnlessRaises(ObjectDoesNotExist, experiments.lanes_for, user)

        response = self.client.get('/experiments/lanes_for/%s/json' % (user,), apidata)
        self.failUnlessEqual(response.status_code, 404)


    def test_raw_data_dir(self):
        """Raw data path generator check"""
        flowcell_id = self.fc1_id
        raw_dir = os.path.join(settings.RESULT_HOME_DIR, flowcell_id)

        fc = models.FlowCell.objects.get(flowcell_id=flowcell_id)
        self.failUnlessEqual(fc.get_raw_data_directory(), raw_dir)

        fc.flowcell_id = flowcell_id + " (failed)"
        self.failUnlessEqual(fc.get_raw_data_directory(), raw_dir)


    def test_data_run_import(self):
        srf_file_type = models.FileType.objects.get(name='SRF')
        runxml_file_type = models.FileType.objects.get(name='run_xml')
        flowcell_id = self.fc1_id
        flowcell = models.FlowCell.objects.get(flowcell_id=flowcell_id)
        flowcell.update_data_runs()
        self.failUnlessEqual(len(flowcell.datarun_set.all()), 1)

        run = flowcell.datarun_set.all()[0]
        result_files = run.datafile_set.all()
        result_dict = dict(((rf.relative_pathname, rf) for rf in result_files))

        srf4 = result_dict['FC12150/C1-37/woldlab_070829_SERIAL_FC12150_4.srf']
        self.failUnlessEqual(srf4.file_type, srf_file_type)
        self.failUnlessEqual(srf4.library_id, '11060')
        self.failUnlessEqual(srf4.data_run.flowcell.flowcell_id, 'FC12150')
        self.failUnlessEqual(
            srf4.data_run.flowcell.lane_set.get(lane_number=4).library_id,
            '11060')
        self.failUnlessEqual(
            srf4.pathname,
            os.path.join(settings.RESULT_HOME_DIR, srf4.relative_pathname))

        lane_files = run.lane_files()
        self.failUnlessEqual(lane_files[4]['srf'], srf4)

        runxml= result_dict['FC12150/C1-37/run_FC12150_2007-09-27.xml']
        self.failUnlessEqual(runxml.file_type, runxml_file_type)
        self.failUnlessEqual(runxml.library_id, None)


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
            self.failUnlessEqual(response.status_code, 200)
            mimetype = f.file_type.mimetype
            if mimetype is None:
                mimetype = 'application/octet-stream'

            self.failUnlessEqual(mimetype, response['content-type'])

class TestFileType(TestCase):
    def test_file_type_unicode(self):
        file_type_objects = models.FileType.objects
        name = 'QSEQ tarfile'
        file_type_object = file_type_objects.get(name=name)
        self.failUnlessEqual(u"<FileType: QSEQ tarfile>",
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
            self.failUnlessEqual(ft['file_type'],
                                 file_type_objects.get(name=typename))
            self.failUnlessEqual(ft.get('lane', None), lane)
            self.failUnlessEqual(ft.get('end', None), end)

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
            self.failUnlessEqual(result['file_type'],
                                 file_type_objects.get(name=typename))
            self.failUnlessEqual(result.get('lane',None), lane)
            self.failUnlessEqual(result.get('end', None), end)

class TestEmailNotify(TestCase):
    fixtures = ['test_flowcells.json']

    def test_started_email_not_logged_in(self):
        response = self.client.get('/experiments/started/153/')
        self.failUnlessEqual(response.status_code, 302)

    def test_started_email_logged_in_user(self):
        self.client.login(username='test', password='BJOKL5kAj6aFZ6A5')
        response = self.client.get('/experiments/started/153/')
        self.failUnlessEqual(response.status_code, 302)

    def test_started_email_logged_in_staff(self):
        self.client.login(username='admintest', password='BJOKL5kAj6aFZ6A5')
        response = self.client.get('/experiments/started/153/')
        self.failUnlessEqual(response.status_code, 200)

    def test_started_email_send(self):
        self.client.login(username='admintest', password='BJOKL5kAj6aFZ6A5')
        response = self.client.get('/experiments/started/153/')
        self.failUnlessEqual(response.status_code, 200)

        self.failUnless('pk1@example.com' in response.content)
        self.failUnless('Lane #8 : (11064) Paired ends 104' in response.content)

        response = self.client.get('/experiments/started/153/', {'send':'1','bcc':'on'})
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(len(mail.outbox), 4)
        for m in mail.outbox:
            self.failUnless(len(m.body) > 0)

    def test_email_navigation(self):
        """
        Can we navigate between the flowcell and email forms properly?
        """
        self.client.login(username='supertest', password='BJOKL5kAj6aFZ6A5')
        response = self.client.get('/experiments/started/153/')
        self.failUnlessEqual(response.status_code, 200)
        self.failUnless(re.search('Flowcell FC12150', response.content))
        # require that navigation back to the admin page exists
        self.failUnless(re.search('<a href="/admin/experiments/flowcell/153/">[^<]+</a>', response.content))

def multi_lane_to_dict(lane):
    """Convert a list of lane entries into a dictionary indexed by library ID
    """
    return dict( ((x['library_id'],x) for x in lane) )
