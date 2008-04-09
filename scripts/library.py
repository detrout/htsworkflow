import datetime
from optparse import OptionParser
from pprint import pprint
import sqlite3
import sys
import time

class fctracker:
    def __init__(self):
        self.conn = sqlite3.connect('fctracker.db')
        self._get_library()
        self._get_species()

    def _make_dict_from_table(self, table_name, pkey_name):
        table = {}
        c = self.conn.cursor()
        c.execute('select * from %s;' % (table_name))
        # extract just the field name
        description = [ f[0] for f in c.description]
        for row in c:
            row_dict = dict(zip(description, row))
            table[row_dict[pkey_name]] = row_dict
        c.close()
        return table

    def _get_library(self):
        self.library = self._make_dict_from_table(
                         'fctracker_library', 
                         'library_id')
                                                  
        
    def _get_species(self):
        self.species = self._make_dict_from_table(
                         'fctracker_species',
                         'id'
                       )
        
    def _get_flowcells(self, where=None):
        if where is None:
            where = ""
        self.flowcells = {}
        c = self.conn.cursor()
        c.execute('select * from fctracker_flowcell %s;' % (where))
        # extract just the field name
        description = [ f[0] for f in c.description ]
        for row in c:
            row_dict = dict(zip(description, row))
            for lane in [ 'lane_%d_library' % (i) for i in range(1,9) ]:
                lane_library = self.library[row_dict[lane+"_id"]]
                species_id = lane_library['library_species_id']
                lane_library['library_species'] = self.species[species_id]
                row_dict[lane] = lane_library
            # some useful parsing
            run_date = time.strptime(row_dict['run_date'],  '%Y-%m-%d %H:%M:%S')
            run_date = datetime.datetime(*run_date[:6])
            row_dict['run_date'] = run_date
            self.flowcells[row_dict['flowcell_id']] = row_dict
        return self.flowcells


def flowcell_gone(name):
    if 'failed' in name:
        return True
    if 'deleted' in name:
        return True
    if 'not run' in name:
        return True
    return False

def report(flowcells):
    flowcell_list = []
    for key, cell in flowcells.items():
        flowcell_list.append( (cell['run_date'], key) )
    flowcell_list.sort()
    for run_date, flowcell_id in flowcell_list:
        cell = flowcells[flowcell_id]
        if flowcell_gone(cell['flowcell_id']):
            continue
        #pprint(cell)
        #print cell['flowcell_id'], cell['run_date']
        for l in range(1,9):
            lane = 'lane_%d' % (l)
            print cell['run_date'].strftime('%y-%b-%d'),
            print cell['flowcell_id'],
            #print "  ",
            print l,cell['%s_library'%(lane)]['library_name'],
            print '(%s)' % (cell['%s_library_id'%(lane)]),
            print cell['%s_library'%(lane)]['library_species']['scientific_name']

def make_parser():
    """
    Make parser
    """
    parser = OptionParser()
    parser.add_option("-w", "--where", dest="where",
                      help="add a where clause",
                      default=None)
    return parser

def main(argv=None):
    if argv is None:
        argv = []
    parser = make_parser()

    opt, args = parser.parse_args(argv)
    
    fc = fctracker()
    cells = fc._get_flowcells(opt.where)

    report(cells)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
