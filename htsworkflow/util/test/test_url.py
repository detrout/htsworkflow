from unittest import TestCase

from htsworkflow.util.url import normalize_url, parse_ssh_url

class TestURLUtilities(TestCase):
    def test_normalize_url(self):

        self.assertEqual(normalize_url('caltech.edu'), 
                         'http://caltech.edu')
        self.assertEqual(normalize_url('http://caltech.edu'),
                         'http://caltech.edu')
        self.assertEqual(normalize_url("foo.com/a/b/c/d/e/f.html"),
                         'http://foo.com/a/b/c/d/e/f.html')
        self.assertEqual(normalize_url("foo.com", "https"),
                         'https://foo.com')
        self.assertEqual(normalize_url(None),
                         None)

    def test_parse_ssh_url(self):

        u = parse_ssh_url('me@caltech.edu:/test/path')
        self.assertEqual(u.user, 'me')
        self.assertEqual(u.host, 'caltech.edu')
        self.assertEqual(u.path, '/test/path')

        u = parse_ssh_url('caltech.edu:path@there')
        self.assertEqual(u.user, None)
        self.assertEqual(u.host, 'caltech.edu')
        self.assertEqual(u.path, 'path@there')

        u = parse_ssh_url('caltech.edu:C:/me/@work')
        self.assertEqual(u.user, None)
        self.assertEqual(u.host, 'caltech.edu')
        self.assertEqual(u.path, 'C:/me/@work')

        self.assertRaises(ValueError, parse_ssh_url, 'hello')
        
def suite():
    from unittest import TestSuite, defaultTestLoader
    suite = TestSuite()
    suite.addTests(defaultTestLoader.loadTestsFromTestCase(TestURLUtilities))
    return suite

if __name__ == '__main__':
    from unittest import main
    main(defaultTest="suite")
