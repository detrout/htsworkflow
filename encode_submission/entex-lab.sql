\pset format unaligned
\pset fieldsep '\t'
with donor as (
  select uri as Donor,
         payload->>'accession'
  from item
  ),
  experiment as (
  select uri as Experiment,
         payload->>'accession' as Experiment_Accession,
         payload->>'description' as Experiment_Description,
         payload->>'status' as Experiment_Status,
         payload->>'date_released' as Experiment_Released,
         payload->>'lab' as Experiment_Lab,
         jsonb_array_elements_text(payload->'replicates') as Replicate
  from item
  where object_type = 'Experiment'
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
           jsonb_array_elements_text(payload->'aliases') as Library_Alias
    from item
    where object_type = 'Library'
  ),
  biosample as (
     select uri as Biosample,
            payload->>'accession' as Biosample_Accession,
            payload->>'date_created' as Biosample_Created,
            payload->>'donor' as Donor
     from item
     where object_type = 'Biosample'
  )
select Experiment_Lab, Experiment_Status, count(Experiment_Accession)
from experiment
     LEFT JOIN replicate ON experiment.Replicate = replicate.Replicate
     LEFT JOIN library on replicate.Library = library.Library
     LEFT JOIN biosample on library.Biosample = biosample.Biosample
where biosample.Donor in ('/human-donors/ENCDO845WKR/','/human-donors/ENCDO451RUA/','/human-donors/ENCDO793LXB/','/human-donors/ENCDO271OUW/')
group by Experiment_Lab, Experiment_Status
-- order by experiment_released, experiment_status, experiment_accession
-- limit 10



-- ENTEX donors 
