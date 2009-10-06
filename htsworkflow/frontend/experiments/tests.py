import re
try:
    import json
except ImportError, e:
    import simplejson as json
import sys

from django.core import mail
from django.test import TestCase
from htsworkflow.frontend.experiments import models
from htsworkflow.frontend.experiments import experiments
from htsworkflow.frontend.auth import apidata

class ExperimentsTestCases(TestCase):
    fixtures = ['test_flowcells.json']

    def setUp(self):
        pass

    def test_flowcell_information(self):
        """
        Check the code that packs the django objects into simple types.
        """
        for fc_id in [u'303TUAAXX', u"42JTNAAXX", "42JU1AAXX"]:
            fc_dict = experiments.flowcell_information(fc_id)
            fc_django = models.FlowCell.objects.get(flowcell_id=fc_id)
            self.failUnlessEqual(fc_dict['flowcell_id'], fc_id)
            self.failUnlessEqual(fc_django.flowcell_id, fc_id)
            self.failUnlessEqual(fc_dict['sequencer'], fc_django.sequencer.name)
            self.failUnlessEqual(fc_dict['read_length'], fc_django.read_length)
            self.failUnlessEqual(fc_dict['notes'], fc_django.notes)
            self.failUnlessEqual(fc_dict['cluster_station'], fc_django.cluster_station.name)

            for lane in fc_django.lane_set.all():
                lane_dict = fc_dict['lane_set'][lane.lane_number]
                self.failUnlessEqual(lane_dict['cluster_estimate'], lane.cluster_estimate)
                self.failUnlessEqual(lane_dict['comment'], lane.comment)
                self.failUnlessEqual(lane_dict['flowcell'], lane.flowcell.flowcell_id)
                self.failUnlessEqual(lane_dict['lane_number'], lane.lane_number)
                self.failUnlessEqual(lane_dict['library_name'], lane.library.library_name)
                self.failUnlessEqual(lane_dict['library_id'], lane.library.library_id)
                self.failUnlessAlmostEqual(lane_dict['pM'], float(lane.pM))
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
                lane_dict = fc_json['lane_set'][unicode(lane.lane_number)]
                self.failUnlessEqual(lane_dict['cluster_estimate'], lane.cluster_estimate)
                self.failUnlessEqual(lane_dict['comment'], lane.comment)
                self.failUnlessEqual(lane_dict['flowcell'], lane.flowcell.flowcell_id)
                self.failUnlessEqual(lane_dict['lane_number'], lane.lane_number)
                self.failUnlessEqual(lane_dict['library_name'], lane.library.library_name)
                self.failUnlessEqual(lane_dict['library_id'], lane.library.library_id)
                self.failUnlessAlmostEqual(lane_dict['pM'], float(lane.pM))
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
        response = self.client.get(u'/experiments/config/303TUAAXX/json')
        self.failUnlessEqual(response.status_code, 403)

    def test_library_id(self):
        """
        Library IDs should be flexible, so make sure we can retrive a non-numeric ID
        """
        response = self.client.get('/experiments/config/303TUAAXX/json', apidata)
        self.failUnlessEqual(response.status_code, 200)
        flowcell = json.loads(response.content)

        self.failUnlessEqual(flowcell['lane_set']['3']['library_id'], 'SL039')

        response = self.client.get('/samples/library/SL039/json', apidata)
        self.failUnlessEqual(response.status_code, 200)
        library_sl039 = json.loads(response.content)

        self.failUnlessEqual(library_sl039['library_id'], 'SL039')

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
        self.failUnless(re.search('Flowcell 303TUAAXX', response.content))
        # require that navigation back to the admin page exists
        self.failUnless(re.search('<a href="/admin/experiments/flowcell/153/">[^<]+</a>', response.content))
        
