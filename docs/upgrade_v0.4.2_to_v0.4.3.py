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
    
    
    c.execute("""alter table samples_library rename to samples_library_temp;""")
    c.execute("""CREATE TABLE "samples_library" (
    "id" varchar(10) NOT NULL PRIMARY KEY,
    "library_name" varchar(100) NOT NULL UNIQUE,
    "library_species_id" integer NOT NULL REFERENCES "samples_species" ("id"),
    "hidden" bool NOT NULL,
    "account_number" varchar(100) NULL,
    "cell_line_id" integer NULL REFERENCES "samples_cellline" ("id"),
    "condition_id" integer NULL REFERENCES "samples_condition" ("id"),
    "antibody_id" integer NULL REFERENCES "samples_antibody" ("id"),
    "replicate" smallint unsigned NOT NULL,
    "experiment_type_id" integer NOT NULL REFERENCES "samples_experimenttype" ("id"),
    "library_type_id" integer NULL REFERENCES "samples_librarytype" ("id"),
    "creation_date" date NULL,
    "made_for" varchar(50) NOT NULL,
    "made_by" varchar(50) NOT NULL,
    "stopping_point" varchar(25) NOT NULL,
    "amplified_from_sample_id" varchar(10) NULL,
    "undiluted_concentration" decimal NULL,
    "successful_pM" decimal NULL,
    "ten_nM_dilution" bool NOT NULL,
    "gel_cut_size" integer NULL,
    "insert_size" integer NULL,
    "notes" text NOT NULL
);""")
    c.execute("""INSERT INTO samples_library
( id, library_name, library_species_id, hidden, account_number,
  cell_line_id,  condition_id, antibody_id, replicate, 
  experiment_type_id, library_type_id, creation_date, made_for,
  made_by, stopping_point, amplified_from_sample_id, 
  undiluted_concentration, successful_pM, ten_nM_dilution, 
  gel_cut_size, notes )
SELECT 
  id, library_name, library_species_id, hidden, account_number,
  cell_line_id,  condition_id, antibody_id, replicate, 
  experiment_type_id, library_type_id, creation_date, made_for,
  made_by, stopping_point, amplified_from_sample_id, 
  undiluted_concentration, successful_pM, ten_nM_dilution, 
  avg_lib_size, notes
FROM samples_library_temp;
""")    
    c.execute('DROP TABLE samples_library_temp;')
    

    # modify experiments_lane
    c.execute("""alter table experiments_lane rename to experiments_lane_temp;""")
    c.execute('''
CREATE TABLE "experiments_lane" (
    "id" integer NOT NULL PRIMARY KEY,
    "flowcell_id" integer NOT NULL REFERENCES "experiments_flowcell" ("id"),
    "lane_number" integer NOT NULL,
    "library_id" varchar(10) NOT NULL REFERENCES "samples_library" ("id"),
    "pM" decimal NOT NULL,
    "cluster_estimate" integer,
    "status" integer,
    "comment" text
);''')

    c.execute('''
INSERT INTO experiments_lane
( id,  flowcell_id, lane_number, library_id, pM, cluster_estimate, comment)
SELECT 
id, flowcell_id, lane_number, library_id, pM, cluster_estimate, comment
FROM experiments_lane_temp;
''')
    c.execute('DROP TABLE experiments_lane_temp;')
    conn.commit()

if __name__ == "__main__":
    main(sys.argv[1:])
