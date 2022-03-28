from unittest import TestCase

from django.urls import reverse
from htsworkflow.util import api


class testApi(TestCase):
    def test_make_key(self):
        k1 = api.make_django_secret_key()
        k2 = api.make_django_secret_key()

        self.assertTrue(len(k1), 85)
        self.assertTrue(len(k2), 85)
        self.assertTrue(k1 != k2)

    def test_library_url(self):
        django_url = reverse("library_json", kwargs={"library_id": "12345"})
        api_url = api.library_url("", "12345")
        self.assertEqual(django_url, api_url)

    def test_flowcell_url(self):
        django_url = reverse("flowcell_config_json", kwargs={"fc_id": "ABCDEFGH"})
        api_url = api.flowcell_url("", "ABCDEFGH")
        self.assertEqual(django_url, api_url)

    def test_lanes_for_url(self):
        django_url = reverse("lanes_for_json", kwargs={"username": "user_id"})
        api_url = api.lanes_for_user_url("", "user_id")
        self.assertEqual(django_url, api_url)


def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestApi))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
