\pset format unaligned
\pset fieldsep '\t'
with
  experiment as (
  select uri as Experiment,
         payload->>'accession' as Experiment_Accession,
         payload->>'description' as Experiment_Description,
         payload->>'status' as Experiment_Status,
         payload->>'date_released' as Experiment_Released,
         payload->>'assay_title' as Experiment_Type,
         jsonb_array_elements_text(payload->'replicates') as Replicate
  from item
  where object_type = 'Experiment' and
        payload->'lab' @> '"/labs/barbara-wold/"'::jsonb
  --      payload->'lab' @> '"/labs/ali-mortazavi/"'::jsonb
  ),
  replicate as (
    select uri as Replicate,
           payload->>'library' as Library
    from item
    where object_type = 'Replicate'
  ),
  library as (
    select uri as Library,
           payload->>'accession' as Library_Accession,
           payload->>'date_created' as Library_Created,
           payload->>'biosample' as Biosample,
           substring(jsonb_array_elements_text(payload->'aliases') from 'barbara-wold:([0-9]+)')
               as Jumpgate_Library_ID
    from item
    where object_type = 'Library'
  ),
  biosample as (
     select uri as Biosample,
            payload->>'donor' as Donor
        from item
        where object_type = 'Biosample'
  ),
  donor as (
     select uri as Donor,
            payload->>'organism' as Organism
      from item
  )
select distinct Experiment_Accession,
                Experiment_Type,
                Experiment_Description,
                Experiment_Status,
                Experiment_Released,
--                experiment.Replicate,
                Library_Accession,
                library.Biosample,
                donor.Organism,
                to_char(library.Library_Created::date, 'YYYY-MM-DD') as Library_Created,
                Jumpgate_Library_ID
--                samples_library.library_name 
from experiment
     LEFT JOIN replicate ON experiment.Replicate = replicate.Replicate
     LEFT JOIN library on replicate.Library = library.Library
--     LEFT JOIN samples_library on Jumpgate_Library_ID = samples_library.id
     LEFT JOIN biosample on library.Biosample = biosample.Biosample
     LEFT JOIN donor on biosample.Donor = donor.Donor
-- where 
--      Experiment_Status = 'started'
order by experiment_released, experiment_status, experiment_accession
-- limit 10
;
