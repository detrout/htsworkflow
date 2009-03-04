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
    c.execute('drop table fctracker_elandresult');
    c.execute('''CREATE TABLE "experiments_clusterstation" (
      "id" integer NOT NULL PRIMARY KEY,
      "name" varchar(50) NOT NULL UNIQUE);''')
    c.execute('''INSERT INTO experiments_clusterstation (name) values ("station");''')
    c.execute('''CREATE TABLE "experiments_sequencer" (
      "id" integer NOT NULL PRIMARY KEY,
      "name" varchar(50) NOT NULL UNIQUE);''')
    c.execute('''INSERT INTO experiments_sequencer (name) values ("HWI-EAS229");''')

    c.execute('''CREATE TABLE "experiments_flowcell" (
    "id" integer NOT NULL PRIMARY KEY,
    "flowcell_id" varchar(20) NOT NULL UNIQUE,
    "run_date" datetime NOT NULL,
    "advanced_run" bool NOT NULL,
    "paired_end" bool NOT NULL,
    "read_length" integer NOT NULL,
    "lane_1_library_id" integer NOT NULL REFERENCES "samples_library" ("id"),
    "lane_2_library_id" integer NOT NULL REFERENCES "samples_library" ("id"),
    "lane_3_library_id" integer NOT NULL REFERENCES "samples_library" ("id"),
    "lane_4_library_id" integer NOT NULL REFERENCES "samples_library" ("id"),
    "lane_5_library_id" integer NOT NULL REFERENCES "samples_library" ("id"),
    "lane_6_library_id" integer NOT NULL REFERENCES "samples_library" ("id"),
    "lane_7_library_id" integer NOT NULL REFERENCES "samples_library" ("id"),
    "lane_8_library_id" integer NOT NULL REFERENCES "samples_library" ("id"),
    "lane_1_pM" decimal NOT NULL,
    "lane_2_pM" decimal NOT NULL,
    "lane_3_pM" decimal NOT NULL,
    "lane_4_pM" decimal NOT NULL,
    "lane_5_pM" decimal NOT NULL,
    "lane_6_pM" decimal NOT NULL,
    "lane_7_pM" decimal NOT NULL,
    "lane_8_pM" decimal NOT NULL,
    "lane_1_cluster_estimate" integer NULL,
    "lane_2_cluster_estimate" integer NULL,
    "lane_3_cluster_estimate" integer NULL,
    "lane_4_cluster_estimate" integer NULL,
    "lane_5_cluster_estimate" integer NULL,
    "lane_6_cluster_estimate" integer NULL,
    "lane_7_cluster_estimate" integer NULL,
    "lane_8_cluster_estimate" integer NULL,
    "cluster_station_id" integer NOT NULL REFERENCES "experiments_clusterstation" ("id"),
    "sequencer_id" integer NOT NULL REFERENCES "experiments_sequencer" ("id"),
    "notes" text NOT NULL
);''')
    c.execute('''insert into experiments_flowcell 
        (id, flowcell_id, run_date, advanced_run, paired_end, read_length,
         lane_1_library_id, lane_2_library_id, lane_3_library_id,
         lane_4_library_id, lane_5_library_id, lane_6_library_id,
         lane_7_library_id, lane_8_library_id, lane_1_pm,
         lane_2_pM, lane_3_pM, lane_4_pM, lane_5_pM, lane_6_pM,
         lane_7_pM, lane_8_pM, lane_1_cluster_estimate,
         lane_2_cluster_estimate, lane_3_cluster_estimate, 
         lane_4_cluster_estimate, lane_5_cluster_estimate,
         lane_6_cluster_estimate, lane_7_cluster_estimate, 
         lane_8_cluster_estimate, cluster_station_id, sequencer_id,
         notes) 
      select
         id, flowcell_id, run_date, advanced_run, paired_end, read_length,
         lane_1_library_id, lane_2_library_id, lane_3_library_id,
         lane_4_library_id, lane_5_library_id, lane_6_library_id,
         lane_7_library_id, lane_8_library_id, lane_1_pm,
         lane_2_pM, lane_3_pM, lane_4_pM, lane_5_pM, lane_6_pM,
         lane_7_pM, lane_8_pM, lane_1_cluster_estimate,
         lane_2_cluster_estimate, lane_3_cluster_estimate, 
         lane_4_cluster_estimate, lane_5_cluster_estimate,
         lane_6_cluster_estimate, lane_7_cluster_estimate, 
         lane_8_cluster_estimate, 1, 1,
         notes from fctracker_flowcell;''')
    c.execute('''drop table fctracker_flowcell;''')

    # create samples.cellline
    c.execute('''CREATE TABLE "samples_cellline" (
    "id" integer NOT NULL PRIMARY KEY,
    "cellline_name" varchar(100) NOT NULL UNIQUE,
    "nickname" varchar(20) NULL,
    "notes" text NOT NULL);''')
    c.execute('''insert into samples_cellline (cellline_name,notes) values("Unknown","Unknown");''')

    # Create samples.condition
    c.execute('''CREATE TABLE "samples_condition" (
    "id" integer NOT NULL PRIMARY KEY,
    "condition_name" varchar(2000) NOT NULL UNIQUE,
    "nickname" varchar(20) NULL,
    "notes" text NOT NULL);''')
    c.execute('''insert into samples_condition (condition_name,notes) values("Unknown","Unknown");''')

    # create samples.library
    c.execute('''CREATE TABLE "samples_library" (
    "id" integer NOT NULL PRIMARY KEY,
    "library_id" varchar(30) NOT NULL,
    "library_name" varchar(100) NOT NULL UNIQUE,
    "library_species_id" integer NOT NULL REFERENCES "samples_species" ("id"),
    "cell_line_id" integer NOT NULL REFERENCES "samples_cellline" ("id"),
    "condition_id" integer NOT NULL REFERENCES "samples_condition" ("id"),
    "antibody_id" integer NULL REFERENCES "samples_antibody" ("id"),
    "replicate" smallint unsigned NOT NULL,
    "experiment_type" varchar(50) NOT NULL,
    "creation_date" date NULL,
    "made_for" varchar(50) NOT NULL,
    "made_by" varchar(50) NOT NULL,
    "stopping_point" varchar(25) NOT NULL,
    "amplified_from_sample_id" integer NULL,
    "undiluted_concentration" decimal NULL,
    "successful_pM" decimal NULL,
    "ten_nM_dilution" bool NOT NULL,
    "avg_lib_size" integer NULL,
    "notes" text NOT NULL);''')
    c.execute('''INSERT INTO samples_library 
      (id,library_id,library_name,library_species_id, experiment_type,
       cell_line_id,condition_id,replicate,made_by,creation_date,
       made_for,stopping_point,amplified_from_sample_id,
       undiluted_concentration,ten_nM_dilution,successful_pM,
       avg_lib_size,notes) 
select library_id,library_id,library_name,library_species_id,"unknown",
       1,           1,           1,        made_by,creation_date,
       made_for,stopping_point,amplified_from_sample_id,
       undiluted_concentration,ten_nM_dilution,successful_pM,
       0,notes from fctracker_library;''');
    c.execute('''update samples_library set experiment_type="RNA-seq" where library_id in (select library_id from fctracker_library where RNASeq = 1);''')
    #c.execute('''drop table fctracker_library;''') 
    # add many to many tables
    c.execute('''CREATE TABLE "samples_library_affiliations" (
    "id" integer NOT NULL PRIMARY KEY,
    "library_id" integer NOT NULL REFERENCES "samples_library" ("id"),
    "affiliation_id" integer NOT NULL REFERENCES "samples_affiliation" ("id"),
    UNIQUE ("library_id", "affiliation_id"));''')

    c.execute('''CREATE TABLE "samples_library_tags" (
    "id" integer NOT NULL PRIMARY KEY,
    "library_id" integer NOT NULL REFERENCES "samples_library" ("id"),
    "tag_id" integer NOT NULL REFERENCES "samples_tag" ("id"),
    UNIQUE ("library_id", "tag_id"));''')



    #
    c.execute('''CREATE TABLE "samples_species" (
    "id" integer NOT NULL PRIMARY KEY,
    "scientific_name" varchar(256) NOT NULL,
    "common_name" varchar(256) NOT NULL);''')
    c.execute('''insert into samples_species 
        (id, scientific_name, common_name)
    select
         id, scientific_name, common_name
    from fctracker_species;''')
    c.execute('''drop table fctracker_species''')
    conn.commit()

if __name__ == "__main__":
    main(sys.argv[1:])
