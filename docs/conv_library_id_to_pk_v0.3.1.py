import optparse
import sqlite3

def map_library_ids(c):
    lib_ids = {}
    c.execute("""select id, library_id from samples_library""")
    for row in c:
        surrogate_id = unicode(row[0]) # auto key
        artificial_id = unicode(row[1]) # the id printed on the library tubes
        lib_ids[surrogate_id] = artificial_id
    return lib_ids

def convert_experiments_lane(c, lib_ids):
    """
    Change Library ID in experiments_lane table
    """
    c.execute('alter table experiments_lane rename to old_experiments_lane')
    c.execute("""CREATE TABLE "experiments_lane" (
    "id" integer NOT NULL PRIMARY KEY,
    "flowcell_id" integer NOT NULL REFERENCES "experiments_flowcell" ("id"),
    "lane_number" integer NOT NULL,
    "library_id" varchar(10) NOT NULL REFERENCES "samples_library" ("library_id"),
    "pM" decimal NOT NULL,
    "cluster_estimate" integer,
    "comment" text);""")

    c.execute("""select id, flowcell_id, lane_number, library_id, pM, cluster_estimate, comment
                 from old_experiments_lane;""")

    new_rows = []
    for row in c:
        new_rows.append({'id':row[0], 'flowcell_id':row[1], 'lane_number':row[2],
                         'library_id':lib_ids[unicode(row[3])], 'pM':row[4],
                         'cluster_estimate':row[5],
                         'comment':row[6]})

    sql = '''insert into experiments_lane
        (id, flowcell_id, lane_number, library_id, pM, cluster_estimate, comment)
        values
        (:id, :flowcell_id, :lane_number, :library_id, :pM, :cluster_estimate, :comment)'''
    c.executemany(sql, new_rows)

    c.execute('drop table old_experiments_lane')

def convert_samples_library_affiliations(c, lib_ids):
    """
    Change Library ID in experiments_lane table
    """
    c.execute('alter table samples_library_affiliations rename to old_samples_library_affiliations')
    c.execute('''CREATE TABLE "samples_library_affiliations" (
    "id" integer NOT NULL PRIMARY KEY,
    "library_id" varchar(10) NOT NULL REFERENCES "samples_library" ("id"),
    "affiliation_id" integer NOT NULL REFERENCES "samples_affiliation" ("id"),
    UNIQUE ("library_id", "affiliation_id")
);''')

    c.execute("""select id, library_id, affiliation_id
                 from old_samples_library_affiliations;""")

    new_rows = []
    for row in c:
        new_rows.append({'id':row[0], 'library_id': lib_ids[unicode(row[1])], 'affiliation_id':row[2],})

    sql = '''insert into samples_library_affiliations
        (id, library_id, affiliation_id)
        values
        (:id, :library_id, :affiliation_id)'''
    c.executemany(sql, new_rows)

    c.execute('drop table old_samples_library_affiliations;')

def convert_samples_library_tags(c, lib_ids):
    """
    Change Library ID in samples_library_tags table
    """
    c.execute('alter table samples_library_tags rename to old_samples_library_tags')
    c.execute('''CREATE TABLE "samples_library_tags" (
    "id" integer NOT NULL PRIMARY KEY,
    "library_id" varchar(10) NOT NULL REFERENCES "samples_library" ("id"),
    "tag_id" integer NOT NULL REFERENCES "samples_tag" ("id"),
    UNIQUE ("library_id", "tag_id")
);''')

    c.execute("""select id, library_id, tag_id
                 from old_samples_library_tags;""")

    new_rows = []
    for row in c:
        new_rows.append({'id':row[0], 'library_id': lib_ids[unicode(row[1])], 'tag_id':row[2]})

    sql = '''insert into samples_library_tags
        (id, library_id, tag_id)
        values
        (:id, :library_id, :tag_id)'''
    c.executemany(sql, new_rows)

    c.execute('drop table old_samples_library_tags;')    


def convert_samples_library(c, lib_ids):
    """
    Change Library ID in samples_library_tags table
    """
    c.execute('alter table samples_library rename to old_samples_library')
    c.execute('''CREATE TABLE "samples_library" (
    "id" varchar(10) NOT NULL PRIMARY KEY,
    "library_name" varchar(100) NOT NULL UNIQUE,
    "library_species_id" integer NOT NULL REFERENCES "samples_species" ("id"),
    "hidden" bool NOT NULL,
    "account_number" varchar(100),
    "cell_line_id" integer REFERENCES "samples_cellline" ("id"),
    "condition_id" integer REFERENCES "samples_condition" ("id"),
    "antibody_id" integer REFERENCES "samples_antibody" ("id"),
    "replicate" smallint unsigned NOT NULL,
    "experiment_type_id" integer NOT NULL REFERENCES "samples_experimenttype" ("id"),
    "library_type_id" integer REFERENCES "samples_librarytype" ("id"),
    "creation_date" date,
    "made_for" varchar(50) NOT NULL,
    "made_by" varchar(50) NOT NULL,
    "stopping_point" varchar(25) NOT NULL,
    "amplified_from_sample_id" varchar(10),
    "undiluted_concentration" decimal,
    "successful_pM" decimal,
    "ten_nM_dilution" bool NOT NULL,
    "avg_lib_size" integer,
    "notes" text NOT NULL
);''')

    c.execute("""
    select library_id, library_name, library_species_id, hidden, account_number, cell_line_id,
    condition_id, antibody_id, replicate, experiment_type_id, library_type_id,
    creation_date, made_for, made_by, stopping_point, amplified_from_sample_id,
    undiluted_concentration, successful_pM, ten_nM_dilution, avg_lib_size, notes
    from old_samples_library;""")

    new_rows = []
    for row in c:
        new_rows.append({
        'id': row[0],
        'library_name': row[1],
        'library_species_id': row[2],
        'hidden': row[3],
        'account_number': row[4],
        'cell_line_id': row[5],
        'condition_id': row[6],
        'antibody_id': row[7],
        'replicate': row[8],
        'experiment_type_id': row[9],
        'library_type_id': row[10],
        'creation_date': row[11],
        'made_for': row[12],
        'made_by': row[13],
        'stopping_point': row[14],
        'amplified_from_sample_id': row[15],
        'undiluted_concentration': row[16],
        'successful_pM': row[17],
        'ten_nM_dilution': row[18],
        'avg_lib_size': row[19],
        'notes': row[20],
            })

    sql = '''insert into samples_library
        (id, library_name, library_species_id, hidden, account_number, cell_line_id,
         condition_id, antibody_id, replicate, experiment_type_id, library_type_id,
         creation_date, made_for, made_by, stopping_point, amplified_from_sample_id,
         undiluted_concentration, successful_pM, ten_nM_dilution, avg_lib_size, notes)
        values
        (:id, :library_name, :library_species_id, :hidden, :account_number, :cell_line_id,
         :condition_id, :antibody_id, :replicate, :experiment_type_id, :library_type_id,
         :creation_date, :made_for, :made_by, :stopping_point, :amplified_from_sample_id,
         :undiluted_concentration, :successful_pM, :ten_nM_dilution, :avg_lib_size, :notes);
         '''
    c.executemany(sql, new_rows)

    c.execute('drop table old_samples_library;')

def convert_library_id(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    lib_ids = map_library_ids(c)

    convert_experiments_lane(c, lib_ids)
    convert_samples_library_affiliations(c, lib_ids)
    convert_samples_library_tags(c, lib_ids)
    convert_samples_library(c, lib_ids)
    
    conn.commit()

def make_parser():
    usage = '%prog: database_filename'
    parser = optparse.OptionParser(usage)
    return parser

def main(cmdline=None):
    parser = make_parser()
    opts, args = parser.parse_args(cmdline)
    if len(args) != 1:
       parser.error('requires path to sqlite database file')

    db_path = args[0]

    convert_library_id(db_path)

if __name__ == "__main__":
    main()
