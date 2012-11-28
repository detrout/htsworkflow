from unittest2 import TestCase

from htsworkflow.automation import solexa

class testSolexaRunfolderUtils(TestCase):
    def test_is_runfolder(self):
        self.failUnlessEqual(solexa.is_runfolder(""), False)
        self.failUnlessEqual(solexa.is_runfolder("1345_23"), False)
        self.failUnlessEqual(solexa.is_runfolder("123456_asdf-$23'"), False)
        self.failUnlessEqual(solexa.is_runfolder("123456_USI-EAS44"), True)
        self.failUnlessEqual(solexa.is_runfolder("123456_USI-EAS44 "), False)


    def test_get_top_dir(self):
        test_data = [ # root, path, response
                      ('/a/b/c', '/a/b/c/d/e/f', 'd'),
                      ('/a/b/c/', '/a/b/c/d/e/f', 'd'),
                      ('/a/b/c', '/g/e/f', None),
                      ('/a/b/c', '/a/b/c', ''),
                    ]
        
        for root, path, response in test_data:
            self.failUnlessEqual(solexa.get_top_dir(root, path), response)
            

def suite():
    from unittest2 import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(testSolexaRunfolderUtils))
    return suite


if __name__ == "__main__":
    from unittest2 import main
    main(defaultTest="suite")
