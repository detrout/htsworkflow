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
    select uri as AntibodyCharacterization,
           payload->>'status' as Status,
           payload->>'characterization_method' as Characterization_Method
    from item
    where object_type = 'AntibodyCharacterization'
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
           payload->>'summary' as Summary,
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
select distinct 
                Experiment_Accession,
                Experiment_Type,
                Experiment_Description,
                Experiment_Status,
                Experiment_Released,
                Library_Accession,
                AntibodyLot,
                Antigen_Description,
                Clonality,
                antibody_characterization.Status as Characterization_Status,
                antibody_characterization.characterization_method as Characterization_Method,
                target.Target,
                target.title as Target_Title,
                target.status as Target_Status,
                biosample.Biosample,
                biosample.summary as Biosample_Description
from experiment
     JOIN replicate ON experiment.Replicate = replicate.Replicate
     JOIN antibody_lot on replicate.Antibody = antibody_lot.AntibodyLot
     JOIN target ON antibody_lot.Target = target.Target
     JOIN library on replicate.Library = library.Library
     JOIN biosample on library.Biosample = biosample.Biosample
     JOIN antibody_characterization on antibody_lot.Characterization = antibody_characterization.AntibodyCharacterization
-- where 
--      Experiment_Status = 'started'
order by experiment_accession, AntibodyLot
-- limit 10
;
