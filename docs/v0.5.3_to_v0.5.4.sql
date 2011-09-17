-- Add fields to support multiplexing, and update our database

alter table samples_library add column multiplex_id varchar(128);
alter table samples_librarytype add column can_multiplex bool not null default false;
alter table samples_librarytype add column is_paired_end bool not null default false;
update samples_librarytype set can_multiplex=0, is_paired_end=0;
update samples_librarytype set can_multiplex=1 where id in (5,7,8);
update samples_librarytype set is_paired_end=1 where id in (2,5,7,8);
update samples_library set multiplex_id=1 where library_name like "Index #1 %";
update samples_library set multiplex_id=2 where library_name like "Index #2 %";
update samples_library set multiplex_id=3 where library_name like "Index #3 %";
update samples_library set multiplex_id=4 where library_name like "Index #4 %";
update samples_library set multiplex_id=5 where library_name like "Index #5 %";
update samples_library set multiplex_id=6 where library_name like "Index #6 %";
update samples_library set multiplex_id=7 where library_name like "Index #7 %";
update samples_library set multiplex_id=8 where library_name like "Index #8 %";
update samples_library set multiplex_id=9 where library_name like "Index #9 %";
update samples_library set multiplex_id=10 where library_name like "Index #10 %";
update samples_library set multiplex_id=11 where library_name like "Index #11 %";
update samples_library set multiplex_id=12 where library_name like "Index #12 %";

update samples_library set multiplex_id=1 where library_name like "Nextera #1 %";
update samples_library set multiplex_id=2 where library_name like "Nextera #2 %";
update samples_library set multiplex_id=3 where library_name like "Nextera #3 %";
update samples_library set multiplex_id=4 where library_name like "Nextera #4 %";
update samples_library set multiplex_id=5 where library_name like "Nextera #5 %";
update samples_library set multiplex_id=6 where library_name like "Nextera #6 %";
update samples_library set multiplex_id=7 where library_name like "Nextera #7 %";
update samples_library set multiplex_id=8 where library_name like "Nextera #8 %";
update samples_library set multiplex_id=9 where library_name like "Nextera #9 %";
update samples_library set multiplex_id=10 where library_name like "Nextera #10 %";
update samples_library set multiplex_id=11 where library_name like "Nextera #11 %";
update samples_library set multiplex_id=12 where library_name like "Nextera #12 %";

update samples_library set multiplex_id=1 where library_name like "Nextera index1 %";
update samples_library set multiplex_id=2 where library_name like "Nextera index2 %";
update samples_library set multiplex_id=3 where library_name like "Nextera index3 %";
update samples_library set multiplex_id=4 where library_name like "Nextera index4 %";
update samples_library set multiplex_id=5 where library_name like "Nextera index5 %";
update samples_library set multiplex_id=6 where library_name like "Nextera index6 %";
update samples_library set multiplex_id=7 where library_name like "Nextera index7 %";
update samples_library set multiplex_id=8 where library_name like "Nextera index8 %";
update samples_library set multiplex_id=9 where library_name like "Nextera index9 %";
update samples_library set multiplex_id=10 where library_name like "Nextera index10 %";
update samples_library set multiplex_id=11 where library_name like "Nextera index11 %";
update samples_library set multiplex_id=12 where library_name like "Nextera index12 %";
