"""
Provide some quick and dirty access and reporting for the fctracker database.

The advantage to this code is that it doesn't depend on django being
installed, so it can run on machines other than the webserver.
"""
import datetime
import os
import re
import sys
import time

if sys.version_info[0] + sys.version_info[1] * 0.1 >= 2.5:
  # we're python 2.5
  import sqlite3
else:
  import pysqlite2.dbapi2 as sqlite3


class fctracker:
    """
    provide a simple way to interact with the flowcell data in fctracker.db
    """
    def __init__(self, database):
        # default to the current directory
        if database is None: 
            self.database = self._guess_fctracker_path()
        else:
            self.database = database
        self.conn = sqlite3.connect(self.database)
        self._get_library()
        self._get_species()

    def _guess_fctracker_path(self):
        """
        Guess a few obvious places for the database
        """
        fctracker = 'fctracker.db'
        name = fctracker
        # is it in the current dir?
        if os.path.exists(name): 
            return name
        name = os.path.expanduser(os.path.join('~', fctracker))
        if os.path.exists(name):
            return name
        raise RuntimeError("Can't find fctracker")

    def _make_dict_from_table(self, table_name, pkey_name):
        """
        Convert a django table into a dictionary indexed by the primary key.
        Yes, it really does just load everything into memory, hopefully
        we stay under a few tens of thousands of runs for a while.
        """
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

    def _add_lanes_to_libraries(self):
        """
        add flowcell/lane ids to new attribute 'lanes' in the library dictionary
        """
        library_id_re = re.compile('lane_\d_library_id')

        for fc_id, fc in self.flowcells.items():
            lane_library = [ (x[0][5], x[1]) for x in fc.items() 
                                             if library_id_re.match(x[0]) ]
            for lane, library_id in lane_library:
                if not self.library[library_id].has_key('lanes'):
                    self.library[library_id]['lanes'] = []
                self.library[library_id]['lanes'].append((fc_id, lane))

    def _get_library(self):
        """
        attach the library dictionary to the instance
        """
        self.library = self._make_dict_from_table(
                         'fctracker_library', 
                         'library_id')
                                                  
        
    def _get_species(self):
        """
        attach the species dictionary to the instance
        """
        self.species = self._make_dict_from_table(
                         'fctracker_species',
                         'id'
                       )
        
    def _get_flowcells(self, where=None):
        """
        attach the flowcell dictionary to the instance

        where is a sql where clause. (eg "where run_date > '2008-1-1'")
        that can be used to limit what flowcells we select
        FIXME: please add sanitization code
        """
        if where is None:
            where = ""
        self.flowcells = {}
        c = self.conn.cursor()
        c.execute('select * from fctracker_flowcell %s;' % (where))
        # extract just the field name
        description = [ f[0] for f in c.description ]
        for row in c:
            row_dict = dict(zip(description, row))
            fcid, status = self._parse_flowcell_id(row_dict)
            row_dict['flowcell_id'] = fcid
            row_dict['flowcell_status'] = status

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

        self._add_lanes_to_libraries()
        return self.flowcells

    def _parse_flowcell_id(self, flowcell_row):
      """
      Return flowcell id and status
      
      We stored the status information in the flowcell id name.
      this was dumb, but database schemas are hard to update.
      """
      fields = flowcell_row['flowcell_id'].split()
      fcid = None
      status = None
      if len(fields) > 0:
        fcid = fields[0]
      if len(fields) > 1:
        status = fields[1]
      return fcid, status
      

def flowcell_gone(cell):
    """
    Use a variety of heuristics to determine if the flowcell drive
    has been deleted.
    """
    status = cell['flowcell_status']
    if status is None:
        return False
    failures = ['failed', 'deleted', 'not run']
    for f in failures:
      if re.search(f, status):
        return True
    else:
      return False

def recoverable_drive_report(flowcells):
    """
    Attempt to report what flowcells are still on a hard drive
    """
    def format_status(status):
      if status is None:
        return ""
      else:
        return status+" "

    # sort flowcells by run date
    flowcell_list = []
    for key, cell in flowcells.items():
        flowcell_list.append( (cell['run_date'], key) )
    flowcell_list.sort()

    report = []
    line = "%(date)s %(id)s %(status)s%(lane)s %(library_name)s (%(library_id)s) "
    line += "%(species)s"
    for run_date, flowcell_id in flowcell_list:
        cell = flowcells[flowcell_id]
        if flowcell_gone(cell):
            continue
        for l in range(1,9):
            lane = 'lane_%d' % (l)
            cell_library = cell['%s_library'%(lane)]
            fields = {
              'date': cell['run_date'].strftime('%y-%b-%d'),
              'id': cell['flowcell_id'],
              'lane': l,
              'library_name': cell_library['library_name'],
              'library_id': cell['%s_library_id'%(lane)],
              'species': cell_library['library_species']['scientific_name'],
              'status': format_status(cell['flowcell_status']),
            }
            report.append(line % (fields))
    return os.linesep.join(report)

