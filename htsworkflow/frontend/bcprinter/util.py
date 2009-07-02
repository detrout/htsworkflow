from htsworkflow.frontend import settings

import ftplib
import socket
import StringIO


def print_zpl(zpl_text, host=settings.BCPRINTER_PRINTER1_HOST):
    """
    Sends zpl_text to printer
    """
    ftp = ftplib.FTP(host=host, user='blank', passwd='')
    ftp.login()
    ftp.storlines("STOR printme.txt", StringIO.StringIO(zpl_text))
    ftp.quit()
    

def print_zpl_socket(zpl_text, host=settings.BCPRINTER_PRINTER1_HOST, port=settings.BCPRINTER_PRINTER1_PORT):
    """
    Sends zpl_text to printer via a socket
    """
    s = socket.socket()
    # PORT 9100 is default for Zebra tabletop/desktop printers
    # PORT 6101 is default for Zebra mobile printers
    s.connect((host, port))
    s.sendall(zpl_text)
    s.close()