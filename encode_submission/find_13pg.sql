-- Look for the 13 pg samples
\pset format unaligned
\pset fieldsep '\t'
with
  experiment as (
  select uri as Experiment,
         payload->>'accession' as Experiment_Accession,
         payload->>'description' as Experiment_Description,
         payload->>'status' as Experiment_Status,
         payload->>'lab' as lab,
         payload->>'date_released' as Experiment_Released,
         payload->>'assay_title' as Experiment_Type,
         jsonb_array_elements_text(payload->'replicates') as Replicate
  from item
  ),
  replicate as (
    select uri as Replicate,
           payload->>'library' as Library,
           payload->>'experiment' as Experiment,
           payload->>'antibody' as Antibody
    from item
    where object_type = 'Replicate'
  ),
  library as (
    select uri as Library,
           payload->>'accession' as Library_Accession,
           payload->>'date_created' as Library_Created,
           payload->>'biosample' as Biosample,
           payload->>'nucleic_acid_starting_quantity' as starting_amount,
           payload->>'nucleic_acid_starting_quantity_units' as starting_amount_units
    from item
    where object_type = 'Library'
  )
select distinct
  experiment.Experiment,
  -- lab,
  Experiment_Description,
  --replicate.Replicate,
  library.Library,
  starting_amount,
  starting_amount_units
  -- biosample_term_name,
  -- antibody_lot.Characterization,
  -- Characterization_Method,
  -- Characterization_Status,
  -- target.title,
--                experiment.Replicate,
--                Library_Accession,
--                library.Biosample,
--                donor.Organism,
--                to_char(library.Library_Created::date, 'YYYY-MM-DD') as Library_Created
from library
     left join replicate on replicate.Library = library.Library
     left join experiment on replicate.Experiment = experiment.Experiment
where starting_amount_units = 'cell-equivalent' and
      starting_amount in ('1', '1.0') 
order by experiment.Experiment, library.Library
;
