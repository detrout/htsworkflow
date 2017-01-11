-- \pset format unaligned
-- \pset fieldsep '\t'
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
        payload->'lab' @> '"/labs/michael-snyder/"'::jsonb
  ),
  replicate as (
    select uri as Replicate,
           payload->>'library' as Library,
           payload->>'antibody' as Antibody
    from item
    where object_type = 'Replicate'
  ),
  antibody_lot as (
    select uri as AntibodyLot,
           payload->>'antigen_description' as Antigen_Description,
           payload->>'clonality' as clonality,
           jsonb_array_elements_text(payload->'targets') as Target,
           jsonb_array_elements_text(payload->'characterizations') as Characterization
    from item
    where object_type = 'AntibodyLot'
  ),
  antibody_characterization as (
    select uri as AntibodyCharacterization
    from item
    where object_type = 'AntibodyCharcterization'
  ),
  library as (
    select uri as Library,
           payload->>'accession' as Library_Accession,
           payload->>'date_created' as Library_Created,
           payload->>'biosample' as Biosample
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
select
  Experiment,
  Experiment_Status,
  Replicate.Replicate,
  Replicate.Antibody,
  AntibodyLot
from experiment
     JOIN replicate ON experiment.Replicate = replicate.Replicate
     JOIN antibody_lot on replicate.Antibody = antibody_lot.AntibodyLot
-- limit 10
;
