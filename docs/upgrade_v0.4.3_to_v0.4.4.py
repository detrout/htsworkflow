"""
This renames avg_lib_size to gel_cut_size and adds an insert length field 
to samples_library.
"""

import shutil
import sqlite3
import sys

def main(cmdline=None):
    if len(cmdline) == 1:
       dest='/tmp/fctracker.db'
    else:
      dest = cmdline[1]
    shutil.copy(cmdline[0], dest)
    conn = sqlite3.connect(dest)
    c = conn.cursor()
    
    c.execute("""
alter table samples_library 
add column "bioanalyzer_concentration" decimal;
""")
    
    c.execute("""
alter table samples_library 
add column "bioanalyzer_summary" text NOT NULL default "";
""")

    c.execute("""
alter table samples_library 
add column "bioanalyzer_image_url" varchar(200) NOT NULL default "";
""")

    conn.commit()

if __name__ == "__main__":
    main(sys.argv[1:])
