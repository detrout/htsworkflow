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
  """
  name = ""
  while len(name) == 0:
    base, name = os.path.split(base)
    if len(base) == 0:
      return None
  return name

def make_commands(run_name, lanes, site_name, destdir, cmdlevel=ILLUMINA2SRF11):
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
  logging.info("run_name %s" % ( run_name, ))
  
  cmd_list = []
  for lane in lanes:
    name_prefix = '%s_%%l_%%t_' % (run_name,)
    destname = '%s_%s_%d.srf' % (site_name, run_name, lane)
    destdir = os.path.normpath(destdir)
    dest_path = os.path.join(destdir, destname)
    seq_pattern = 's_%d_*_seq.txt' % (lane,)

    if cmdlevel == SOLEXA2SRF:
        cmd = ['solexa2srf', 
               '-N', name_prefix,
               '-n', '%3x:%3y', 
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

def run_srf_commands(bustard_dir, cmd_list, num_jobs):
    logging.info("chdir to %s" % (bustard_dir,))
    curdir = os.getcwd()
    os.chdir(bustard_dir)
    q = queuecommands.QueueCommands(cmd_list, num_jobs)
    q.run()
    os.chdir(curdir)
    
