"""Wrap ucsc command line utilities
"""

import logging
import os
import sys
from subprocess import Popen, PIPE

LOGGER = logging.getLogger(__name__)

def parseNumber(number):
    buffer = []
    isFloat = False
    for n in number:
        if n == ',':
            continue
        if n == '.':
            isFloat = True
            buffer.append(n)
        else:
            buffer.append(n)
    if isFloat:
        return float(''.join(buffer))
    else:
        return int(''.join(buffer))

def parseBoolean(value):
    if value.lower() in ('yes', '1', 'true'):
        return True
    elif value.lower() in ('no', '0', 'false'):
        return False
        
class bigWigInfo:
    def __init__(self, filename=None):
        self.version = None
        self.isCompressed = None
        self.isSwapped = None
        self.primaryDataSize = None
        self.primaryIndexSize = None
        self.zoomLevels = None
        self.chromCount = None
        self.basesCovered = None
        self.mean = None
        self.min = None
        self.max = None
        self.std = None
        self.filename = None
        if filename:
            self.scan_file(filename)
            self.filename = filename

    def scan_file(self, filename):
        cmd = ['bigWigInfo', 
               filename]
        try:
            p = Popen(cmd, stdout=PIPE)
            stdout, _ = p.communicate()
            for line in stdout.split(os.linesep):
                if len(line) > 0:
                    term, value = line.split(': ')
                    if term in ('isCompressed', 'isSwapped'):
                        value = parseBoolean(value)
                    else:
                        value = parseNumber(value)
                    LOGGER.debug('%s: %s', term, str(value))
                    setattr(self, term, value)
        except OSError as e:
            LOGGER.error("Exception %s trying to run: %s", str(e), ' '.join(cmd))
            sys.exit(-1)

                
                

