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
    select uri as Characterization,
           payload->>'caption' as Caption,
           payload->>'characterization_method' as Characterization_Method,
           payload->>'status' as Characterization_Status
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
  target as (
    select uri as Target,
           payload->>'title' as title,
           payload->>'status' as status,
           jsonb_array_elements_text(payload->'investigated_as') as investigated_as
    from item
    where object_type = 'Target'
  ),  
  donor as (
     select uri as Donor,
            payload->>'organism' as Organism
      from item
  )
select
  Replicate,
  Library,
  AntibodyLot,
  Antigen_Description,
  Clonality,
  antibody_lot.Target,
  antibody_lot.Characterization,
  Characterization_Method,
  Characterization_Status,
  target.title,
  target.status,
  target.investigated_as
--                experiment.Replicate,
--                Library_Accession,
--                library.Biosample,
--                donor.Organism,
--                to_char(library.Library_Created::date, 'YYYY-MM-DD') as Library_Created
from replicate
     left join antibody_lot on replicate.Antibody = antibody_lot.AntibodyLot
     left join antibody_characterization on
               antibody_lot.Characterization = antibody_characterization.Characterization
     left join target on antibody_lot.Target = target.Target
limit 10
;
