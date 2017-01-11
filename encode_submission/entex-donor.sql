-- \pset format unaligned
-- \pset fieldsep '\t'
with gtex as (
  select distinct uri as Donor,
         substring(jsonb_array_elements_text(payload->'aliases'), '([a-zA-Z0-9]+):') as AliasPrefix
  from item
  where object_type = 'HumanDonor'
  )
select Donor, AliasPrefix
from gtex
where AliasPrefix = 'gtex'
;
