import os
import sys
import logging

LOGGER = logging.getLogger(__name__)

try:
    import py_sg
    
    
    def get_hd_serial_num(device):
        """
        device = '/dev/sdX'
        
        returns hard drive serial number for a device; requires read permissions.
        """
        fd = os.open(device, os.O_RDONLY)
        
        # fd: device object
        # \x12: INQUIRY CMD; \x01: EVPD bit set to 1; \x80: Unit Serial Number page
        #  See http://en.wikipedia.org/wiki/SCSI_Inquiry_Command for helpful chart
        # ##: # byte buffer for returned data
        data = py_sg.read(fd, "\x12\x01\x80", 32)
        
        # Remove extra \x00's, and split remaining data into two chunks,
        #  the 2nd of which is the serial number
        return data.strip('\x00').split()[1]
    
except ImportError as e:
    LOGGER.error("hdquery requires py_sg")

    def get_hd_serial_num(device):
        raise NotImplemented('get_hd_serial_num is not available for anything other than linux')
    
