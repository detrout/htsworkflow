import RDF

from django.test import TestCase
from django.test.utils import setup_test_environment, \
     teardown_test_environment
from django.db import connection
from django.conf import settings

from django.contrib.auth.models import User
from django.core import urlresolvers

from htsworkflow.frontend.inventory.models import Item, Vendor
from htsworkflow.util.rdfhelp import get_model, load_string_into_model, get_serializer, inventoryOntology, libraryOntology, fromTypedNode

def localhostNode(url):
    return RDF.Node(RDF.Uri('http://localhost%s' % (url,)))

class InventoryTestCase(TestCase):
    fixtures = ['test_user', 'test_harddisks']

    def test_fixture(self):
        # make sure that some of our test data is was loaded
        # since there was no error message when I typoed the test fixture
        hd1 = Item.objects.get(pk=1)
        self.failUnlessEqual(hd1.uuid, '8a90b6ce522311de99b00015172ce556')

        user = User.objects.get(pk=5)
        self.failUnlessEqual(user.username, 'test')

    def test_item(self):
        url = '/inventory/8a90b6ce522311de99b00015172ce556/'
        self.client.login(username='test', password='BJOKL5kAj6aFZ6A5')
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        model = get_model()
        load_string_into_model(model, 'rdfa', response.content, url)

        itemNode = RDF.Node(RDF.Uri(url))
        item_type = fromTypedNode(model.get_target(itemNode, inventoryOntology['item_type']))
        self.failUnlessEqual(item_type, u'Hard Drive')

    def test_itemindex(self):
        url = '/inventory/it/Hard Drive/'
        indexNode = localhostNode(url)
        diskNode = localhostNode('/inventory/8a90b6ce522311de99b00015172ce556/')
        self.client.login(username='test', password='BJOKL5kAj6aFZ6A5')

        flowcells = self.get_flowcells_from_content(url, indexNode, diskNode)
        self.failUnlessEqual(len(flowcells), 2)
        self.failUnless('http://localhost/flowcell/11ONEAAXX/' in flowcells)
        self.failUnless('http://localhost/flowcell/22TWOAAXX/' in flowcells)

    def test_add_disk(self):
        url = '/inventory/it/Hard Drive/'
        #url_disk = '/inventory/8a90b6ce522311de99b00015172ce556/'
        url_disk = '/inventory/b0792d425aa411de99b00015172ce556/'
        indexNode = localhostNode(url)
        diskNode = localhostNode(url_disk)
        self.client.login(username='test', password='BJOKL5kAj6aFZ6A5')

        flowcells = self.get_flowcells_from_content(url, indexNode, diskNode)
        self.failUnlessEqual(len(flowcells), 0)

        # step two link the flowcell
        flowcell = '22TWOAAXX'
        serial = 'WCAU49042470'
        link_url = urlresolvers.reverse(
                'htsworkflow.frontend.inventory.views.link_flowcell_and_device',
                args=(flowcell, serial))
        link_response = self.client.get(link_url)
        self.failUnlessEqual(link_response.status_code, 200)

        flowcells = self.get_flowcells_from_content(url, indexNode, diskNode)
        self.failUnlessEqual(len(flowcells), 1)
        self.failUnlessEqual('http://localhost/flowcell/%s/' % (flowcell),
                             flowcells[0])

    def test_add_disk_failed_flowcell(self):
        url = '/inventory/it/Hard Drive/'
        #url_disk = '/inventory/8a90b6ce522311de99b00015172ce556/'
        url_disk = '/inventory/b0792d425aa411de99b00015172ce556/'
        indexNode = localhostNode(url)
        diskNode = localhostNode(url_disk)
        self.client.login(username='test', password='BJOKL5kAj6aFZ6A5')

        flowcells = self.get_flowcells_from_content(url, indexNode, diskNode)
        self.failUnlessEqual(len(flowcells), 0)

        # step two link the flowcell
        flowcell = '33THRAAXX'
        serial = 'WCAU49042470'
        link_url = urlresolvers.reverse(
                'htsworkflow.frontend.inventory.views.link_flowcell_and_device',
                args=(flowcell, serial))
        link_response = self.client.get(link_url)
        self.failUnlessEqual(link_response.status_code, 200)

        flowcells = self.get_flowcells_from_content(url, indexNode, diskNode)
        self.failUnlessEqual(len(flowcells), 1)
        self.failUnlessEqual('http://localhost/flowcell/%s/' % (flowcell),
                             flowcells[0])


    def get_flowcells_from_content(self, url, rootNode, diskNode):
        model = get_model()

        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        load_string_into_model(model, 'rdfa', response.content, rootNode.uri)
        targets = model.get_targets(diskNode, libraryOntology['flowcell_id'])
        flowcells = [ str(x.uri) for x in targets]
        return flowcells

def suite():
    from unittest2 import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(InventoryTestCase))
    return suite

if __name__ == "__main__":
    from unittest2 import main
    main(defaultTest="suite")
