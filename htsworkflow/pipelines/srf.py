from glob import glob
import logging
import os

from htsworkflow.util import queuecommands

SOLEXA2SRF = 0
ILLUMINA2SRF10 = 1
ILLUMINA2SRF11 = 2

def pathname_to_run_name(base):
  """
  Convert a pathname to a base runfolder name
  handle the case with a trailing /

  >>> print pathname_to_run_name("/a/b/c/run")
  run
  >>> print pathname_to_run_name("/a/b/c/run/")
  run
  >>> print pathname_to_run_name("run")
  run
  >>> print pathname_to_run_name("run/")
  run
  >>> print pathname_to_run_name("../run")
  run
  >>> print pathname_to_run_name("../run/")
  run
  """
  name = ""
  while len(name) == 0:
    base, name = os.path.split(base)
    if len(base) == 0:
      break
  return name

def make_srf_commands(run_name, bustard_dir, lanes, site_name, destdir, cmdlevel=ILLUMINA2SRF11):
  """
  make a subprocess-friendly list of command line arguments to run solexa2srf
  generates files like:
  woldlab:080514_HWI-EAS229_0029_20768AAXX:8.srf
   site        run name                    lane

  run_name - most of the file name (run folder name is a good choice)
  lanes - list of integers corresponding to which lanes to process
  site_name - name of your "sequencing site" or "Individual"
  destdir - where to write all the srf files
  """
  # clean up pathname
  logging.info("run_name %s" % (run_name,))

  cmd_list = []
  for lane in lanes:
    name_prefix = '%s_%%l_' % (run_name,)
    destname = '%s_%s_%d.srf' % (site_name, run_name, lane)
    destdir = os.path.normpath(destdir)
    dest_path = os.path.join(destdir, destname)
    seq_pattern = 's_%d_*_seq.txt' % (lane,)

    if cmdlevel == SOLEXA2SRF:
        cmd = ['solexa2srf',
               '-N', name_prefix,
               '-n', '%t:%3x:%3y',
               '-o', dest_path,
               seq_pattern]
    elif cmdlevel == ILLUMINA2SRF10:
        cmd = ['illumina2srf',
               '-v1.0',
               '-o', dest_path,
               seq_pattern]
    elif cmdlevel == ILLUMINA2SRF11:
        seq_pattern = 's_%d_*_qseq.txt' % (lane,)
        cmd = ['illumina2srf',
               '-o', dest_path,
               seq_pattern]
    else:
        raise ValueError("Unrecognized run level %d" % (cmdlevel,))

    logging.info("Generated command: " + " ".join(cmd))
    cmd_list.append(" ".join(cmd))
  return cmd_list

def create_qseq_patterns(bustard_dir):
    """Scan a bustard directory for qseq files and determine a glob pattern
    """
    # grab one tile for each lane.
    qseqs = glob(os.path.join(bustard_dir, '*_1101_qseq.txt'))
    # handle old runfolders
    if len(qseqs) == 0:
      qseqs = glob(os.path.join(bustard_dir, '*_0001_qseq.txt'))
    if len(qseqs) == 0:
      r
    qseqs = [ os.path.split(x)[-1] for x in qseqs ]
    if len(qseqs[0].split('_')) == 4:
      # single ended
      return [(None, "s_%d_[0-9][0-9][0-9][0-9]_qseq.txt")]
    elif len(qseqs[0].split('_')) == 5:
      # more than 1 read
      # build a dictionary of read numbers by lane
      # ( just in case we didn't run all 8 lanes )
      lanes = {}
      for q in qseqs:
        sample, lane, read, tile, extension = q.split('_')
        lanes.setdefault(lane, []).append(read)
      qseq_patterns = []
      # grab a lane from the dictionary
      # I don't think it matters which one.
      k = lanes.keys()[0]
      # build the list of patterns
      for read in lanes[k]:
        read = int(read)
        qseq_patterns.append((read, 's_%d_' + '%d_[0-9][0-9][0-9][0-9]_qseq.txt' % (read,)))
      return qseq_patterns
    else:
      raise RuntimeError('unrecognized qseq pattern, not a single or multiple read pattern')

def make_qseq_commands(run_name, bustard_dir, lanes, site_name, destdir, cmdlevel=ILLUMINA2SRF11):
  """
  make a subprocess-friendly list of command line arguments to run solexa2srf
  generates files like:
  woldlab:080514_HWI-EAS229_0029_20768AAXX:8.srf
   site        run name                    lane

  run_name - most of the file name (run folder name is a good choice)
  lanes - list of integers corresponding to which lanes to process
  site_name - name of your "sequencing site" or "Individual"
  destdir - where to write all the srf files
  """
  # clean up pathname
  logging.info("run_name %s" % (run_name,))

  cmd_list = []
  for lane in lanes:
    name_prefix = '%s_%%l_%%t_' % (run_name,)
    destdir = os.path.normpath(destdir)
    qseq_patterns = create_qseq_patterns(bustard_dir)

    for read, pattern in qseq_patterns:
      if read is None:
        destname = '%s_%s_l%d.tar.bz2' % (site_name, run_name, lane)
        dest_path = os.path.join(destdir, destname)
      else:
        destname = '%s_%s_l%d_r%d.tar.bz2' % (site_name, run_name, lane, read)
        dest_path = os.path.join(destdir, destname)

      cmd = " ".join(['tar', 'cjf', dest_path, pattern % (lane,) ])
      logging.info("Generated command: " + cmd)
      cmd_list.append(cmd)

  return cmd_list

def run_commands(new_dir, cmd_list, num_jobs):
    logging.info("chdir to %s" % (new_dir,))
    curdir = os.getcwd()
    os.chdir(new_dir)
    q = queuecommands.QueueCommands(cmd_list, num_jobs)
    q.run()
    os.chdir(curdir)

def make_md5_commands(destdir):
  """
  Scan the cycle dir and create md5s for the contents
  """
  cmd_list = []
  destdir = os.path.abspath(destdir)
  bz2s = glob(os.path.join(destdir, "*.bz2"))
  gzs = glob(os.path.join(destdir, "*gz"))
  srfs = glob(os.path.join(destdir, "*.srf"))

  file_list = bz2s + gzs + srfs

  for f in file_list:
      cmd = " ".join(['md5sum', f, '>', f + '.md5'])
      logging.info('generated command: ' + cmd)
      cmd_list.append(cmd)

  return cmd_list

