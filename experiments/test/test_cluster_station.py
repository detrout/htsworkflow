from __future__ import absolute_import, print_function, unicode_literals

from django.test import TestCase
from ..models import ClusterStation, cluster_station_default
from ..experiments_factory import ClusterStationFactory

class ClusterStationTestCase(TestCase):
    def test_default(self):
        """test when there are no default cluster stations
        """
        c = ClusterStationFactory(isdefault=False)
        c.isdefault = False
        c.save()

        total = ClusterStation.objects.filter(isdefault=True).count()
        self.assertEqual(total, 0)


    def test_update_default(self):
        """make sure there is only one default cluster station
        """
        old_default = ClusterStationFactory()
        self.assertEqual(old_default.isdefault, True)
        old_default.save()

        new_default = ClusterStationFactory()
        self.assertEqual(new_default.isdefault, True)
        new_default.save()

        c = cluster_station_default()
        self.assertEqual(c.isdefault, True)
        self.assertNotEqual(old_default, new_default)
        self.assertEqual(new_default, c)

        total = ClusterStation.objects.filter(isdefault=True).count()
        self.assertEqual(total, 1)

    def test_update_other(self):
        old_default = ClusterStationFactory()
        old_default.save()
        total = ClusterStation.objects.filter(isdefault=True).count()
        self.assertEqual(total, 1)

        c = ClusterStation.objects.get(pk=old_default.id)
        c.name = "Primary Key 1"
        c.save()

        total = ClusterStation.objects.filter(isdefault=True).count()
        self.assertEqual(total, 1)

        new_default = cluster_station_default()
        self.assertEqual(old_default, new_default)


def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(ClusterStationTestCase))
    return suite

if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
