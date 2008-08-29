"""
Utility functions to make bedfiles.
"""
import os
import re

# map eland_result.txt sense 
sense_map = { 'F': '+', 'R': '-'}
sense_color = { 'F': '0,0,255', 'R': '255,255,0' }

def write_bed_header(outstream, name, description):
  """
  Produce the headerline for a bedfile
  """
  # provide default track names
  if name is None: name = "track"
  if description is None: description = "eland result file"
  bed_header = 'track name="%s" description="%s" visibility=4 itemRgb="ON"'
  bed_header += os.linesep
  outstream.write(bed_header % (name, description))

def make_bed_from_eland_stream(instream, outstream, name, description, chromosome_prefix='chr'):
  """
  read an eland result file from instream and write a bedfile to outstream
  """
  # indexes into fields in eland_result.txt file
  SEQ = 1
  CHR = 6
  START = 7
  SENSE = 8

  write_bed_header(outstream, name, description)

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


def make_bed_from_multi_eland_stream(
  instream, 
  outstream, 
  name, 
  description, 
  chr_prefix='chr', 
  max_reads=255
  ):
  """
  read a multi eland stream and write a bedfile
  """
  write_bed_header(outstream, name, description)
  parse_multi_eland(instream, outstream, chr_prefix, max_reads)

def parse_multi_eland(instream, outstream, chr_prefix, max_reads=255):

  loc_pattern = '(?P<fullloc>(?P<start>[0-9]+)(?P<dir>[FR])(?P<count>[0-9]+))'
  other_pattern = '(?P<chr>[^:,]+)'
  split_re = re.compile('(%s|%s)' % (loc_pattern, other_pattern))

  for line in instream:
    rec = line.split()
    if len(rec) > 3:
      # colony_id = rec[0]
      seq = rec[1]
      # number of matches for 0, 1, and 2 mismatches
      # m0, m1, m2 = [int(x) for x in rec[2].split(':')]
      compressed_reads = rec[3]
      cur_chr = ""
      reads = {0: [], 1: [], 2:[]}

      for token in split_re.finditer(compressed_reads):
        if token.group('chr') is not None:
          cur_chr =  token.group('chr')[:-3] # strip off .fa
        elif token.group('fullloc') is not None:
          matches = int(token.group('count'))
          # only emit a bed line if 
          #  our current chromosome starts with chromosome pattern
          if chr_prefix is None or cur_chr.startswith(chr_prefix):
            start = int(token.group('start'))
            stop = start + len(seq)
            orientation = token.group('dir')
            strand = sense_map[orientation]
            color = sense_color[orientation]
            # build up list of reads for this record
            reads[matches].append((cur_chr, start, stop, strand, color))

      # report up to our max_read threshold reporting the fewer-mismatch
      # matches first
      reported_reads = 0
      keys = [0,1,2]
      for mismatch, read_list in ((k, reads[k]) for k in keys): 
        reported_reads += len(read_list)
        if reported_reads <= max_reads:
          for cur_chr, start, stop, strand, color in read_list:
            reported_reads += 1
            outstream.write('%s %d %d read 0 %s - - %s%s' % (
                cur_chr,
                start,
                stop,
                sense_map[orientation],
                sense_color[orientation],
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
