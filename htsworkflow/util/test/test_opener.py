from io import BytesIO
import tempfile
from unittest import TestCase

from htsworkflow.util.opener import isfilelike, isurllike, autoopen

class TestOpener(TestCase):
    def test_isfilelike(self):
        self.assertFalse(isfilelike("hello", 'r'))
        self.assertFalse(isfilelike("hello", 'rb'))
        self.assertFalse(isfilelike("hello", 'rt'))

        hello = BytesIO(b"hello")
        self.assertTrue(isfilelike(hello, 'r'))
        self.assertTrue(isfilelike(hello, 'rb'))
        self.assertTrue(isfilelike(hello, 'rt'))

    def test_isurllike(self):
        self.assertFalse(isurllike("/tmp", None))
        self.assertTrue(isurllike("https://example.org", None))
        self.assertTrue(isurllike("ftp://example.org", None))
        self.assertTrue(isurllike("x-test://example.org", None))

    def test_autoopen_stream(self):
        text = b'hello'
        hello = BytesIO(text)
        stream = autoopen(hello)
        self.assertEqual(stream.read(), text)

    def test_autoopen_text_file(self):
        text = 'hello'
        with tempfile.NamedTemporaryFile('wt', prefix='autoopen_') as tempstream:
            tempstream.write(text)
            tempstream.flush()

            stream = autoopen(tempstream.name, 'rt')
            self.assertEqual(stream.read(), text)
