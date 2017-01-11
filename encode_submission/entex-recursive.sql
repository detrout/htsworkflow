-- \pset format unaligned
-- \pset fieldsep '\t'
with recursive
  gtex as (
  select distinct uri as Donor,
         substring(jsonb_array_elements_text(payload->'aliases'), '([a-zA-Z0-9]+):') as AliasPrefix
  from item
  where object_type = 'HumanDonor'
  ),
  biosample(uri, payload, parent_of, part_of, d) as (
       select uri, payload,
              jsonb_array_elements_text(payload->'parent_of') as parent_of,
              payload->>'part_of' as part_of,
              1
       from item
       where object_type = 'Biosample'
   union all
       select uri, payload,
              jsonb_array_elements_text(payload->'parent_of') as parent_of,
              payload->>'part_of' as part_of,
              d + 1
       from biosample
       where parent_of = uri
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
select gtex.Donor, biosample.uri, biosample.parent_of
from gtex
     JOIN biosample ON gtex.Donor = biosample.payload->>'donor'
where gtex.AliasPrefix = 'gtex'
;
