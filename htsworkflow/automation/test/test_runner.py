import unittest


import os
from htsworkflow.automation.copier import runfolder_validate

def extract_runfolder_path(watchdir, event):
  runfolder_path = watchdir
  path = event.path
  if not path.startswith(watchdir):
    return None

  fragments = path[len(watchdir):].split(os.path.sep)
  for f in fragments:
    runfolder_path = os.path.join(runfolder_path, f)
    if runfolder_validate(f):
      return runfolder_path
  return None

class Event(object):
  def __init__(self, path=None, name=None):
    self.path = path
    self.name = name

class testRunner(unittest.TestCase):

    def test_extract_runfolder(self):
        watchdir = os.path.join('root', 'server', 'mount')
        runfolder = os.path.join(watchdir, '080909_HWI-EAS229_0052_1234ABCD')
        ipar = os.path.join(runfolder, 'Data', 'IPAR_1.01')
        other = os.path.join(watchdir, 'other')

        event = Event( path=runfolder )
        self.failUnlessEqual(extract_runfolder_path(watchdir, event), runfolder)
        
        event = Event( path=ipar )
        self.failUnlessEqual(extract_runfolder_path(watchdir, event), runfolder)

        event = Event( path=other)
        self.failUnlessEqual(extract_runfolder_path(watchdir, event), None )
        
def suite():
    return unittest.makeSuite(testRunner,'test')

if __name__ == "__main__":
    unittest.main(defaultTest="suite")
