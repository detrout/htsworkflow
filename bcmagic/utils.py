from __future__ import unicode_literals

from django.conf import settings

import ftplib
import socket
from six.moves import StringIO


def print_zpl(zpl_text, host=None):
    """
    Sends zpl_text to printer
    """
    if not host:
        host = settings.BCPRINTER_PRINTER1_HOST
    ftp = ftplib.FTP(host=host, user='blank', passwd='')
    ftp.login()
    ftp.storlines("STOR printme.txt", StringIO.StringIO(zpl_text))
    ftp.quit()


def print_zpl_socket(zpl_text, host=None, port=None):
    """
    Sends zpl_text to printer via a socket

    if zpl_text is a list of zpl_texts, it will print each one
    in that list.
    """
    
    if not host:
        host=settings.BCPRINTER_PRINTER1_HOST
    if not port:
        port=settings.BCPRINTER_PRINTER1_PORT

    # Process anyway if zpl_text is a list.
    if type(zpl_text) is list:
        zpl_text = '\n'.join(zpl_text)

    s = socket.socket()
    # PORT 9100 is default for Zebra tabletop/desktop printers
    # PORT 6101 is default for Zebra mobile printers
    s.connect((host, port))
    s.sendall(zpl_text.encode("ascii"))
    s.close()


def report_error(message):
    """
    Return a dictionary with a command to display 'message'
    """
    return {'mode': 'Error', 'status': message}


def redirect_to_url(url):
    """
    Return a bcm dictionary with a command to redirect to 'url'
    """
    return {'mode': 'redirect', 'url': url}


def autofill(field, value):
    """
    Return a bcm dictionary with a command to automatically fill the
    corresponding "field" with "value"
    """
    return {'mode': 'autofill', 'field': field, 'value': value}
