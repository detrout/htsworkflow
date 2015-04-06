from __future__ import absolute_import, print_function

import RDF

from django.test import TestCase
from django.test.utils import setup_test_environment, \
     teardown_test_environment
from django.db import connection
from django.conf import settings

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_text

from .models import Item, Vendor
from .inventory_factory import ItemFactory, LongTermStorageFactory
from samples.samples_factory import HTSUserFactory, LibraryFactory
from experiments.experiments_factory import FlowCellFactory
from htsworkflow.util.rdfhelp import get_model, load_string_into_model, get_serializer, inventoryOntology, libraryOntology, fromTypedNode

def localhostNode(url):
    return RDF.Node(RDF.Uri('http://localhost%s' % (url,)))

class InventoryTestCase(TestCase):
    def setUp(self):
        self.password = 'foo'
        self.user = HTSUserFactory.create()
        self.user.set_password(self.password)
        self.user.save()

    def test_item(self):
        item = ItemFactory()
        self.assertTrue(len(item.uuid), 32)
        url = '/inventory/{}/'.format(item.uuid)
        self.assertTrue(self.client.login(username=self.user.username,
                                          password=self.password))
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        content = smart_text(response.content)

        model = get_model()
        load_string_into_model(model, 'rdfa', content, url)

        itemNode = RDF.Node(RDF.Uri(url))
        item_type = fromTypedNode(
            model.get_target(itemNode, inventoryOntology['item_type']))
        self.failUnlessEqual(item_type, item.item_type.name)

    def test_itemindex(self):
        item = ItemFactory()
        fc1 = FlowCellFactory()
        lib1 = LibraryFactory()
        lts = LongTermStorageFactory(flowcell=fc1,
                                     libraries=[lib1,],
                                     storage_devices=[item,],)

        url = reverse('inventory.views.itemtype_index',
                      kwargs={'name': item.item_type.name})
        disk_url = reverse('inventory.views.item_summary_by_uuid',
                           kwargs={'uuid': item.uuid})
        indexNode = localhostNode(url)
        diskNode = localhostNode(disk_url)
        self.assertTrue(self.client.login(username=self.user.username,
                                          password=self.password))

        flowcells = self.get_flowcells_from_content(url, indexNode, diskNode)
        self.failUnlessEqual(len(flowcells), 1)
        flowcell_url = reverse('experiments.views.flowcell_detail',
                               kwargs={'flowcell_id': fc1.flowcell_id})
        self.assertTrue(flowcells[0].endswith(flowcell_url))


    def test_add_disk(self):
        item = ItemFactory()
        url = reverse('inventory.views.itemtype_index',
                      kwargs={'name': item.item_type.name})
        disk_url = reverse('inventory.views.item_summary_by_uuid',
                           kwargs={'uuid': item.uuid})
        indexNode = localhostNode(url)
        diskNode = localhostNode(disk_url)

        self.assertTrue(self.client.login(username=self.user.username,
                                          password=self.password))

        flowcells = self.get_flowcells_from_content(url, indexNode, diskNode)
        self.failUnlessEqual(len(flowcells), 0)

        # step two link the flowcell
        flowcell = FlowCellFactory(flowcell_id='22TWOAAXX')
        link_url = reverse('inventory.views.link_flowcell_and_device',
                           args=(flowcell.flowcell_id,
                                 item.barcode_id))
        link_response = self.client.get(link_url)
        self.assertEqual(link_response.status_code, 200)

        flowcells = self.get_flowcells_from_content(url, indexNode, diskNode)
        flowcell_url = reverse('experiments.views.flowcell_detail',
                               kwargs={'flowcell_id': flowcell.flowcell_id})
        self.assertEqual(len(flowcells), 1)
        self.assertTrue(flowcells[0].endswith(flowcell_url))

    def test_add_disk_failed_flowcell(self):
        item = ItemFactory()
        url = reverse('inventory.views.itemtype_index',
                      kwargs={'name': item.item_type.name})
        disk_url = reverse('inventory.views.item_summary_by_uuid',
                           kwargs={'uuid': item.uuid})
        indexNode = localhostNode(url)
        diskNode = localhostNode(disk_url)

        self.assertTrue(self.client.login(username=self.user.username,
                                          password=self.password))

        flowcells = self.get_flowcells_from_content(url, indexNode, diskNode)
        self.failUnlessEqual(len(flowcells), 0)

        # step two link the flowcell
        flowcell_id = '33THRAAXX'
        flowcell = FlowCellFactory(flowcell_id=flowcell_id +' (failed)')
        link_url = reverse('inventory.views.link_flowcell_and_device',
                           args=(flowcell.flowcell_id, item.barcode_id))
        link_response = self.client.get(link_url)
        self.failUnlessEqual(link_response.status_code, 200)

        flowcells = self.get_flowcells_from_content(url, indexNode, diskNode)
        self.assertEqual(len(flowcells), 1)
        flowcell_url = reverse('experiments.views.flowcell_detail',
                               kwargs={'flowcell_id': flowcell_id})
        self.assertTrue(flowcells[0].endswith(flowcell_url))


    def get_flowcells_from_content(self, url, rootNode, diskNode):
        model = get_model()

        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        content = smart_text(response.content)
        load_string_into_model(model, 'rdfa', content, rootNode.uri)
        targets = model.get_targets(diskNode, libraryOntology['flowcell_id'])
        flowcells = [ str(x.uri) for x in targets]
        return flowcells

def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(InventoryTestCase))
    return suite

if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
