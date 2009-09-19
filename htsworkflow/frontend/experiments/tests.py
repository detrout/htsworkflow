try:
    import json
except ImportError, e:
    import simplejson as json
    
from django.test import TestCase
from htsworkflow.frontend.experiments import models
from htsworkflow.frontend.experiments import experiments

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
                self.failUnlessEqual(lane_dict['library_id'], lane.library_id)
                self.failUnlessAlmostEqual(lane_dict['pM'], float(lane.pM))
                    
            self.client.login(username='test', password='BJOKL5kAj6aFZ6A5')
            response = self.client.get('/experiments/config/%s/json' % (fc_id,))
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
                self.failUnlessEqual(lane_dict['library_id'], lane.library_id)
                self.failUnlessAlmostEqual(lane_dict['pM'], float(lane.pM))

    def test_invalid_flowcell(self):
        """
        Make sure we get a 404 if we request an invalid flowcell ID
        """
        self.client.login(username='test', password='BJOKL5kAj6aFZ6A5')
        response = self.client.get('/experiments/config/nottheone/json')
        self.failUnlessEqual(response.status_code, 404)

    def test_not_logged_in(self):
        """
        Require logging in to retrieve meta data
        """
        response = self.client.get(u'/experiments/config/303TUAAXX/json')
        self.failUnlessEqual(response.status_code, 302)
