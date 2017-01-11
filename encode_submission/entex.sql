\pset format unaligned
\pset fieldsep '\t'
with
  gtex as (
  select distinct uri as Donor,
         substring(jsonb_array_elements_text(payload->'aliases'), '([a-zA-Z0-9]+):') as AliasPrefix
  from item
  where object_type = 'HumanDonor'
  ),
  biosample as (
     select uri as Biosample,
            payload->>'accession' as Biosample_Accession,
            payload->>'date_created' as Biosample_Created,
            payload->>'lab' as Biosample_Lab,
            payload->>'biosample_term_name' as Biosample_Term,
            payload->>'summary' as Description,
            jsonb_array_elements_text(payload->'parent_of') as child_biosample,
            payload->>'donor' as Donor
        from item
        where object_type = 'Biosample'
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
  )
select gtex.Donor, Biosample, Biosample_Lab, Biosample_Term, Description, child_biosample
from gtex
     LEFT JOIN biosample ON gtex.Donor = biosample.Donor
where gtex.AliasPrefix = 'gtex'
;
