"""
Utility functions to make bedfiles.
"""
import os

def make_bed_from_eland_stream(instream, outstream, name, description, chromosome_prefix='chr'):
  """
  read an eland result file from instream and write a bedfile to outstream
  """
  # indexes into fields in eland_result.txt file
  SEQ = 1
  CHR = 6
  START = 7
  SENSE = 8
  # map eland_result.txt sense 
  sense_map = { 'F': '+', 'R': '-'}
  sense_color = { 'F': '0,0,255', 'R': '255,255,0' }
  # provide default track names
  if name is None: name = "track"
  if description is None: description = "eland result file"
  bed_header = 'track name="%s" description="%s" visibility=4 itemRgb="ON"'
  bed_header += os.linesep
  outstream.write(bed_header % (name, description))

  for line in instream:
    fields = line.split()
    # we need more than the CHR field, and it needs to match a chromosome
    if len(fields) <= CHR or \
          (chromosome_prefix is not None and \
             fields[CHR][:3] != chromosome_prefix):
      continue
    start = fields[START]
    stop = int(start) + len(fields[SEQ])
    chromosome, extension = fields[CHR].split('.')
    assert extension == "fa"
    outstream.write('%s %s %d read 0 %s - - %s%s' % (
      chromosome,
      start,
      stop,
      sense_map[fields[SENSE]], 
      sense_color[fields[SENSE]],
      os.linesep  
    ))

def make_description(database, flowcell_id, lane):
    """
    compute a bedfile name and description from the fctracker database
    """
    from gaworkflow.util.fctracker import fctracker

    fc = fctracker(database)
    cells = fc._get_flowcells("where flowcell_id='%s'" % (flowcell_id))
    if len(cells) != 1:
      raise RuntimeError("couldn't find flowcell id %s" % (flowcell_id))
    lane = int(lane)
    if lane < 1 or lane > 8:
      raise RuntimeError("flowcells only have lanes 1-8")

    name = "%s-%s" % (flowcell_id, lane)

    cell_id, cell = cells.items()[0]
    assert cell_id == flowcell_id

    cell_library_id = cell['lane_%d_library_id' %(lane,)]
    cell_library = cell['lane_%d_library' %(lane,)]
    description = "%s-%s" % (cell_library['library_name'], cell_library_id)
    return name, description
