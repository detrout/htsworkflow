-- We need to find Chip Seq experiemnts with more than 2 replicates
--
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
         payload->>'lab' as lab,
         payload->>'award' as award,
         jsonb_array_elements_text(payload->'replicates') as Replicate
  from item
  where object_type = 'Experiment'
  ),
  award as (
  select uri as award_uri,
      payload->>'accession' as Award_Accession,
      payload->>'rfa' as rfa
  from item
  where object_type = 'Award'
  )
--  replicate as (
--    select uri as Replicate,
--           payload->>'library' as Library,
--           payload->>'antibody' as Antibody
--    from item
--    where object_type = 'Replicate'
--  ),
--  antibody_lot as (
--    select uri as AntibodyLot,
--           payload->>'antigen_description' as Antigen_Description,
--           payload->>'clonality' as clonality,
--           jsonb_array_elements_text(payload->'targets') as Target,
--           jsonb_array_elements_text(payload->'characterizations') as Characterization
--    from item
--    where object_type = 'AntibodyLot'
--  ),
--  antibody_characterization as (
--    select uri as AntibodyCharacterization,
--           payload->>'status' as Status,
--           payload->>'characterization_method' as Characterization_Method
--    from item
--    where object_type = 'AntibodyCharacterization'
--  ),
--  library as (
--    select uri as Library,
--           payload->>'accession' as Library_Accession,
--           payload->>'date_created' as Library_Created,
--           payload->>'biosample' as Biosample,
--           jsonb_array_elements_text(payload->'aliases') as lab_alias
--    from item
--    where object_type = 'Library'
--  ),
--  biosample as (
--    select uri as Biosample,
--           payload->>'accession' as Biosample_Accession,
--           payload->>'summary' as Summary,
--           payload->>'donor' as Donor
--    from item
--    where object_type = 'Biosample'
--  ),
--  target as (
--    select uri as Target,
--           payload->>'title' as title,
--           payload->>'status' as status,
--           jsonb_array_elements_text(payload->'investigated_as') as investigated_as
--    from item
--    where object_type = 'Target'
--  ),  
--  donor as (
--     select uri as Donor,
--            payload->>'organism' as Organism
--      from item
--  )
select distinct 
                Experiment_Accession,
                -- Experiment_Type,
                Experiment_Description,
                lab,
                award.rfa as Project,
                -- Experiment_Status,
                -- Experiment_Released,
                -- Library_Accession,
                count(experiment.Replicate)
                -- lab_alias
                -- AntibodyLot,
                -- Antigen_Description,
                -- Clonality,
                -- antibody_characterization.Status as Characterization_Status,
                -- antibody_characterization.characterization_method as Characterization_Method,
                -- target.Target,
                -- target.title as Target_Title,
                -- target.status as Target_Status,
                -- biosample.Biosample_Accession
                -- biosample.summary as Biosample_Description
from experiment
     left JOIN award on experiment.award = award_uri
--     left JOIN replicate ON experiment.Replicate = replicate.Replicate
--     left JOIN library on replicate.Library = library.Library
--     left JOIN antibody_lot on replicate.Antibody = antibody_lot.AntibodyLot
--     left JOIN target ON antibody_lot.Target = target.Target
--     left JOIN biosample on library.Biosample = biosample.Biosample
--     left JOIN antibody_characterization on antibody_lot.Characterization = antibody_characterization.AntibodyCharacterization
where -- lab in ('/labs/barbara-wold/', '/labs/richard-meyers/') and
      experiment_type = 'ChIP-seq'
group by Experiment_Accession, Experiment_Description, lab, project
order by experiment_accession
;
