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
         payload->>'lab' as Lab,
         jsonb_array_elements_text(payload->'replicates') as Replicate
  from item
  where object_type = 'Experiment' and (
        payload->'lab' @> '"/labs/barbara-wold/"'::jsonb OR
        payload->'lab' @> '"/labs/ali-mortazavi/"'::jsonb )
  ),
  replicate as (
    select uri as Replicate,
           payload->>'library' as Library,
           payload->>'antibody' as Antibody
    from item
    where object_type = 'Replicate'
  ),
  library as (
    select uri as Library,
           payload->>'accession' as Library_Accession,
           substring(jsonb_array_elements_text(payload->'aliases') from 'barbara-wold:([0-9]+)')
               as Jumpgate_Library_ID,
           payload->>'date_created' as Library_Created,
           payload->>'biosample' as Biosample
    from item
    where object_type = 'Library'
  ),
  biosample as (
     select uri as Biosample,
            payload->>'accession' as Biosample_Accession,
            substr(payload->>'part_of', 13, 11) as part_of,
            payload->>'donor' as Donor
        from item
        where object_type = 'Biosample'
  )
select distinct
  Biosample_Accession,
  part_of,
  Jumpgate_Library_ID,
  creation_date,
  -- Library_Accession,
  Experiment_Accession,
  -- Experiment_Status,
  Lab
from experiment
     JOIN replicate ON replicate.Replicate = experiment.Replicate
     JOIN library ON replicate.Library = library.Library
     JOIN biosample ON biosample.Biosample = library.Biosample
     left JOIN samples_library on Jumpgate_Library_ID = samples_library.id
-- limit 10
order by Biosample_Accession, part_of, Jumpgate_Library_ID
;
