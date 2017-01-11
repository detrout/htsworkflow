with recursive
   biosample(uri, payload, parent_of, part_of, d) as (
       select uri, payload,
              jsonb_array_elements_text(payload->'parent_of') as parent_of,
              payload->>'part_of' as part_of,
              1
       from item
       where object_type = 'Biosample'
   union all
       select child.uri, child.payload,
              jsonb_array_elements_text(child.payload->'parent_of') as parent_of,
              child.payload->>'part_of' as part_of,
              d + 1
       from biosample, item child
       where biosample.uri = child.payload->>'part_of'
   )
select part_of, uri, parent_of, d
from biosample
where d > 1
order by uri
