with
  annotation as (
  select
    uri as annotation,
    payload->>'description' as description,
    jsonb_array_elements_text(payload->'files') as file
  from item
  where object_type = 'Annotation'
  ),
  file as (
  select
    uri as file,
    payload->>'status' as status,
    payload->>'file_type' as file_type,
    payload->>'file_format' as file_format,
    payload->>'output_type' as output_type,
    payload->>'output_category' as category
  from item
  where object_type = 'File'
  )
select annotation, description, file.file, status, file_type, file_format, category
from annotation
     join file on annotation.file = file.file
where category != 'raw data'
;
