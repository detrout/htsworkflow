from unittest import TestCase

import os
from htsworkflow.automation.solexa import is_runfolder

def extract_runfolder_path(watchdir, event):
  runfolder_path = watchdir
  path = event.path
  if not path.startswith(watchdir):
    return None

  fragments = path[len(watchdir):].split(os.path.sep)
  for f in fragments:
    runfolder_path = os.path.join(runfolder_path, f)
    if is_runfolder(f):
      return runfolder_path
  return None


class Event(object):
  def __init__(self, path=None, name=None):
    self.path = path
    self.name = name


class testRunner(TestCase):
    def test_extract_runfolder(self):
        watchdir = os.path.join('root', 'server', 'mount')
        runfolder = os.path.join(watchdir, '080909_HWI-EAS229_0052_1234ABCD')
        ipar = os.path.join(runfolder, 'Data', 'IPAR_1.01')
        other = os.path.join(watchdir, 'other')

        event = Event( path=runfolder )
        self.assertEqual(extract_runfolder_path(watchdir, event), runfolder)
        
        event = Event( path=ipar )
        self.assertEqual(extract_runfolder_path(watchdir, event), runfolder)

        event = Event( path=other)
        self.assertEqual(extract_runfolder_path(watchdir, event), None )


def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(testRunner))
    return suite


if __name__ == "__main__":
    from unittest import main
    main(defaultTest="suite")
