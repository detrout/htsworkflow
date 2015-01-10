from __future__ import absolute_import, print_function

from django.test import TestCase
from ..models import Sequencer, sequencer_default
from ..experiments_factory import SequencerFactory

class SequencerTestCases(TestCase):
    def test_default(self):
        # starting with no default
        s = SequencerFactory()
        s.save()
        self.assertEqual(s.id, 1)

        total = Sequencer.objects.filter(isdefault=True).count()
        self.assertEqual(total, 1)

        s.isdefault = False
        s.save()

        total = Sequencer.objects.filter(isdefault=True).count()
        self.assertEqual(total, 0)

        other_default = SequencerFactory()
        other_default.save()
        total = Sequencer.objects.filter(isdefault=True).count()
        self.assertEqual(total, 1)


    def test_update_default(self):
        old_default = SequencerFactory()
        old_default.save()

        s = SequencerFactory()
        s.save()

        new_default = sequencer_default()

        self.assertNotEqual(old_default, new_default)
        self.assertEqual(new_default, s)

        total = Sequencer.objects.filter(isdefault=True).count()
        self.assertEqual(total, 1)


    def test_update_other(self):
        old_default = SequencerFactory()
        old_default.save()
        total = Sequencer.objects.filter(isdefault=True).count()
        self.assertEqual(total, 1)

        s = Sequencer.objects.get(pk=old_default.id)
        s.name = "Primary Key 1"
        s.save()

        total = Sequencer.objects.filter(isdefault=True).count()
        self.assertEqual(total, 1)

        new_default = sequencer_default()
        self.assertEqual(old_default, new_default)


def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(SequencerTestCase))
    return suite

if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
