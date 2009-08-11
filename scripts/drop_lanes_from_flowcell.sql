BEGIN TRANSACTION;
CREATE TEMPORARY TABLE experiments_flowcell_temp (
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
);
INSERT INTO experiments_flowcell_temp SELECT id,flowcell_id,run_date,advanced_run,paired_end,read_length,lane_1_library_id,lane_2_library_id,lane_3_library_id,lane_4_library_id,lane_5_library_id,lane_6_library_id,lane_7_library_id,lane_8_library_id,lane_1_pM,lane_2_pM,lane_3_pM,lane_4_pM,lane_5_pM,lane_6_pM,lane_7_pM,lane_8_pM,lane_1_cluster_estimate,lane_2_cluster_estimate,lane_3_cluster_estimate,lane_4_cluster_estimate,lane_5_cluster_estimate,lane_6_cluster_estimate,lane_7_cluster_estimate,lane_8_cluster_estimate,cluster_station_id,sequencer_id,notes FROM experiments_flowcell;
DROP TABLE experiments_flowcell;
CREATE TABLE experiments_flowcell (                                      
    "id" integer NOT NULL PRIMARY KEY,                                     
    "flowcell_id" varchar(20) NOT NULL UNIQUE,                             
    "run_date" datetime NOT NULL,                                          
    "advanced_run" bool NOT NULL,                                          
    "paired_end" bool NOT NULL,                                            
    "read_length" integer NOT NULL,                                        
    "cluster_station_id" integer NOT NULL REFERENCES "experiments_clusterstation" ("id"),
    "sequencer_id" integer NOT NULL REFERENCES "experiments_sequencer" ("id"),
    "notes" text NOT NULL
);
INSERT INTO experiments_flowcell SELECT id,flowcell_id,run_date,advanced_run,paired_end,read_length,cluster_station_id,sequencer_id,notes FROM experiments_flowcell_temp;
DROP TABLE experiments_flowcell_temp;
COMMIT;
