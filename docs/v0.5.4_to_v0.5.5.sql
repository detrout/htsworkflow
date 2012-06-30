drop table experiments_sequencer;
drop table experiments_datafile;
drop table experiments_datarun;
alter table experiments_clusterstation add column isdefault bool not null default false;
select "dont forget to syncdb";