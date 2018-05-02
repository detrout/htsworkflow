from io import BytesIO
import bz2
import gzip
import six
import tempfile
from unittest import TestCase, skipIf
import requests_mock

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

    def test_autoopen_gzip_file(self):
        text = 'hello'
        with tempfile.NamedTemporaryFile('wb', prefix='autoopen_', suffix='.gz') as tempstream:
            tempstream.write(gzip_compress(text.encode()))
            tempstream.flush()

            stream = autoopen(tempstream.name, 'rt')
            self.assertEqual(stream.read(), text)

    def test_autoopen_bzip2_file(self):
        text = 'hello'
        with tempfile.NamedTemporaryFile('wb', prefix='autoopen_', suffix='.bz2') as tempstream:
            tempstream.write(bz2.compress(text.encode()))
            tempstream.flush()

            stream = autoopen(tempstream.name, 'r')
            b = stream.read()
            self.assertEqual(b.decode(), text)

    @skipIf(six.PY2, "gunzipping requiles Python 3")
    def test_autoopen_gzip_http(self):
        text = 'hello'
        with requests_mock.Mocker() as mock:
            hello_gz = gzip_compress(text.encode())
            headers = {'Content-Type': 'application/gzip'}
            mock.register_uri('GET', 'http://localhost/hello.txt.gz', headers=headers, content=hello_gz)
            stream = autoopen('http://localhost/hello.txt.gz', 'rt')
            raw = stream.read()
            print('raw', type(raw))
            self.assertEqual(raw, 'hello')
        print('ran')

def gzip_compress(b):
    string_buffer = BytesIO()
    stream = gzip.GzipFile(mode='wb', fileobj=string_buffer)
    stream.write(b)
    stream.close()
    return string_buffer.getvalue()
