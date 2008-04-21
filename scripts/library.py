"""
Provide some quick and dirty access and reporting for the fctracker database.

The advantage to this code is that it doesn't depend on django being
installed, so it can run on machines other than the webserver.
"""
from optparse import OptionParser
import sys

from gaworkflow.util import fctracker

def make_parser():
    """
    Make parser
    """
    parser = OptionParser()
    parser.add_option("-d", "--database", dest="database",
                      help="path to the fctracker.db",
                      default=None)
    parser.add_option("-w", "--where", dest="where",
                      help="add a where clause",
                      default=None)
    return parser

def main(argv=None):
    if argv is None:
        argv = []
    parser = make_parser()

    opt, args = parser.parse_args(argv)
    
    fc = fctracker.fctracker(opt.database)
    cells = fc._get_flowcells(opt.where)

    print fctracker.recoverable_drive_report(cells)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
