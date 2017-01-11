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
         payload->>'lab' as Experiment_Lab,
         jsonb_array_elements_text(payload->'replicates') as Replicate
  from item
  where object_type = 'Experiment' and
        payload->'lab' @> '"/labs/richard-myers/"'::jsonb
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
           jsonb_array_elements_text(payload->'aliases') as LibraryAlias
    from item
    where object_type = 'Library'
  )
select distinct Experiment_Accession,
                Experiment_Type,
                Experiment_Description,
                Experiment_Status,
                Experiment_Released,
                Experiment_Lab,
--                experiment.Replicate,
                experiment.Replicate,
                Library_Accession,
                to_char(library.Library_Created::date, 'YYYY-MM-DD') as Library_Created,
                LibraryAlias
--                library.Biosample,
from experiment
     LEFT JOIN replicate ON experiment.Replicate = replicate.Replicate
     LEFT JOIN library on replicate.Library = library.Library
-- where 
--      Experiment_Status = 'started'
order by experiment_released, experiment_status, experiment_accession
-- limit 10
;
