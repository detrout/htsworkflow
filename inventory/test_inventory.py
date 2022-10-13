from __future__ import absolute_import, print_function

from django.test import TestCase
from django.test.utils import setup_test_environment, \
     teardown_test_environment
from django.db import connection
from django.conf import settings

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.encoding import smart_str

from rdflib import Graph, Literal, URIRef

from .models import Item, Vendor
from .inventory_factory import ItemFactory, LongTermStorageFactory
from samples.samples_factory import HTSUserFactory, LibraryFactory
from experiments.experiments_factory import FlowCellFactory
from encoded_client.rdfns import inventoryOntology, libraryOntology

def localhostNode(url):
    return URIRef('http://localhost%s' % (url,))

class InventoryTestCase(TestCase):
    def setUp(self):
        self.password = 'foo'
        self.user = HTSUserFactory.create()
        self.user.set_password(self.password)
        self.user.save()

    def test_item(self):
        item = ItemFactory()
        self.assertTrue(len(item.uuid), 32)
        url = reverse("item_summary_by_uuid", args=(item.uuid,))
        self.assertTrue(self.client.login(username=self.user.username,
                                          password=self.password))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = smart_str(response.content)

        model = Graph()
        model.parse(data=content, format="rdfa", media_type="text/html", publicID=url)

        itemNode = URIRef(url)
        items = list(model.objects(itemNode, inventoryOntology['item_type']))
        item_type = items[0].toPython()

        self.assertEqual(item_type, item.item_type.name)

    def test_itemindex(self):
        item = ItemFactory()
        fc1 = FlowCellFactory()
        lib1 = LibraryFactory()
        lts = LongTermStorageFactory(flowcell=fc1,
                                     libraries=[lib1,],
                                     storage_devices=[item,],)

        url = reverse('itemtype_index',
                      kwargs={'name': item.item_type.name})
        disk_url = reverse('item_summary_by_uuid',
                           kwargs={'uuid': item.uuid})
        indexNode = localhostNode(url)
        diskNode = localhostNode(disk_url)
        self.assertTrue(self.client.login(username=self.user.username,
                                          password=self.password))

        flowcells = self.get_flowcells_from_content(url, indexNode, diskNode)
        self.assertEqual(len(flowcells), 1)
        flowcell_url = reverse('flowcell_detail',
                               kwargs={'flowcell_id': fc1.flowcell_id})
        self.assertTrue(flowcells[0].endswith(flowcell_url))


    def test_add_disk(self):
        item = ItemFactory()
        url = reverse('itemtype_index',
                      kwargs={'name': item.item_type.name})
        disk_url = reverse('item_summary_by_uuid',
                           kwargs={'uuid': item.uuid})
        indexNode = localhostNode(url)
        diskNode = localhostNode(disk_url)

        self.assertTrue(self.client.login(username=self.user.username,
                                          password=self.password))

        flowcells = self.get_flowcells_from_content(url, indexNode, diskNode)
        self.assertEqual(len(flowcells), 0)

        # step two link the flowcell
        flowcell = FlowCellFactory(flowcell_id='22TWOAAXX')
        link_url = reverse('link_flowcell_and_device',
                           args=(flowcell.flowcell_id,
                                 item.barcode_id))
        link_response = self.client.get(link_url)
        self.assertEqual(link_response.status_code, 200)

        flowcells = self.get_flowcells_from_content(url, indexNode, diskNode)
        flowcell_url = reverse('flowcell_detail',
                               kwargs={'flowcell_id': flowcell.flowcell_id})
        self.assertEqual(len(flowcells), 1)
        self.assertTrue(flowcells[0].endswith(flowcell_url))

    def test_add_disk_failed_flowcell(self):
        item = ItemFactory()
        url = reverse('itemtype_index', kwargs={'name': item.item_type.name})
        disk_url = reverse('item_summary_by_uuid', kwargs={'uuid': item.uuid})
        indexNode = localhostNode(url)
        diskNode = localhostNode(disk_url)

        self.assertTrue(self.client.login(username=self.user.username,
                                          password=self.password))

        flowcells = self.get_flowcells_from_content(url, indexNode, diskNode)
        self.assertEqual(len(flowcells), 0)

        # step two link the flowcell
        flowcell_id = '33THRAAXX'
        flowcell = FlowCellFactory(flowcell_id=flowcell_id + ' (failed)')
        link_url = reverse('link_flowcell_and_device',
                           args=(flowcell.flowcell_id, item.barcode_id))
        link_response = self.client.get(link_url)
        self.assertEqual(link_response.status_code, 200)

        flowcells = self.get_flowcells_from_content(url, indexNode, diskNode)
        self.assertEqual(len(flowcells), 1)
        flowcell_url = reverse('flowcell_detail',
                               kwargs={'flowcell_id': flowcell_id})
        self.assertTrue(flowcells[0].endswith(flowcell_url))

    def get_flowcells_from_content(self, url, rootNode, diskNode):
        model = Graph()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        content = smart_str(response.content)
        model.parse(data=content, format="rdfa", media_type="text/html", publicID=rootNode)
        targets = model.objects(diskNode, libraryOntology['flowcell_id'])
        flowcells = [ str(x) for x in targets]
        return flowcells

def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(InventoryTestCase))
    return suite

if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
