"""
Core information needed to inspect a runfolder.
"""
from glob import glob
import logging
import os
import re
import shutil
import stat
import subprocess
import sys
import time

try:
  from xml.etree import ElementTree
except ImportError, e:
  from elementtree import ElementTree

EUROPEAN_STRPTIME = "%d-%m-%Y"
EUROPEAN_DATE_RE = "([0-9]{1,2}-[0-9]{1,2}-[0-9]{4,4})"
VERSION_RE = "([0-9\.]+)"
USER_RE = "([a-zA-Z0-9]+)"
LANES_PER_FLOWCELL = 8

from htsworkflow.util.alphanum import alphanum
from htsworkflow.util.ethelp import indent, flatten

class PipelineRun(object):
    """
    Capture "interesting" information about a pipeline run
    """
    XML_VERSION = 1
    PIPELINE_RUN = 'PipelineRun'
    FLOWCELL_ID = 'FlowcellID'

    def __init__(self, pathname=None, xml=None):
        if pathname is not None:
          self.pathname = os.path.normpath(pathname)
        else:
          self.pathname = None
        self._name = None
        self._flowcell_id = None
        self.image_analysis = None
        self.bustard = None
        self.gerald = None

        if xml is not None:
          self.set_elements(xml)

    def _get_flowcell_id(self):
        # extract flowcell ID
        if self._flowcell_id is None:
          config_dir = os.path.join(self.pathname, 'Config')
          flowcell_id_path = os.path.join(config_dir, 'FlowcellId.xml')
	  if os.path.exists(flowcell_id_path):
            flowcell_id_tree = ElementTree.parse(flowcell_id_path)
            self._flowcell_id = flowcell_id_tree.findtext('Text')
	  else:
            path_fields = self.pathname.split('_')
            if len(path_fields) > 0:
              # guessing last element of filename
              flowcell_id = path_fields[-1]
            else:
              flowcell_id = 'unknown'

	    logging.warning(
	      "Flowcell id was not found, guessing %s" % (
	         flowcell_id))
	    self._flowcell_id = flowcell_id
        return self._flowcell_id
    flowcell_id = property(_get_flowcell_id)

    def get_elements(self):
        """
        make one master xml file from all of our sub-components.
        """
        root = ElementTree.Element(PipelineRun.PIPELINE_RUN)
        flowcell = ElementTree.SubElement(root, PipelineRun.FLOWCELL_ID)
        flowcell.text = self.flowcell_id
        root.append(self.image_analysis.get_elements())
        root.append(self.bustard.get_elements())
        root.append(self.gerald.get_elements())
        return root

    def set_elements(self, tree):
        # this file gets imported by all the others,
        # so we need to hide the imports to avoid a cyclic imports
        from htsworkflow.pipelines import firecrest
        from htsworkflow.pipelines import ipar
        from htsworkflow.pipelines import bustard
        from htsworkflow.pipelines import gerald

        tag = tree.tag.lower()
        if tag != PipelineRun.PIPELINE_RUN.lower():
          raise ValueError('Pipeline Run Expecting %s got %s' % (
              PipelineRun.PIPELINE_RUN, tag))
        for element in tree:
          tag = element.tag.lower()
          if tag == PipelineRun.FLOWCELL_ID.lower():
            self._flowcell_id = element.text
          #ok the xword.Xword.XWORD pattern for module.class.constant is lame
          # you should only have Firecrest or IPAR, never both of them.
          elif tag == firecrest.Firecrest.FIRECREST.lower():
            self.image_analysis = firecrest.Firecrest(xml=element)
          elif tag == ipar.IPAR.IPAR.lower():
            self.image_analysis = ipar.IPAR(xml=element)
          elif tag == bustard.Bustard.BUSTARD.lower():
            self.bustard = bustard.Bustard(xml=element)
          elif tag == gerald.Gerald.GERALD.lower():
            self.gerald = gerald.Gerald(xml=element)
          else:
            logging.warn('PipelineRun unrecognized tag %s' % (tag,))

    def _get_run_name(self):
        """
        Given a run tuple, find the latest date and use that as our name
        """
        if self._name is None:
          tmax = max(self.image_analysis.time, self.bustard.time, self.gerald.time)
          timestamp = time.strftime('%Y-%m-%d', time.localtime(tmax))
          self._name = 'run_'+self.flowcell_id+"_"+timestamp+'.xml'
        return self._name
    name = property(_get_run_name)

    def save(self, destdir=None):
        if destdir is None:
            destdir = ''
        logging.info("Saving run report "+ self.name)
        xml = self.get_elements()
        indent(xml)
        dest_pathname = os.path.join(destdir, self.name)
        ElementTree.ElementTree(xml).write(dest_pathname)

    def load(self, filename):
        logging.info("Loading run report from " + filename)
        tree = ElementTree.parse(filename).getroot()
        self.set_elements(tree)

def load_pipeline_run_xml(pathname):
    """
    Load and instantiate a Pipeline run from a run xml file

    :Parameters: 
      - `pathname` : location of an run xml file

    :Returns: initialized PipelineRun object
    """
    tree = ElementTree.parse(pathname).getroot()
    run = PipelineRun(xml=tree)
    return run

def get_runs(runfolder):
    """
    Search through a run folder for all the various sub component runs
    and then return a PipelineRun for each different combination.

    For example if there are two different GERALD runs, this will
    generate two different PipelineRun objects, that differ
    in there gerald component.
    """
    from htsworkflow.pipelines import firecrest
    from htsworkflow.pipelines import ipar
    from htsworkflow.pipelines import bustard
    from htsworkflow.pipelines import gerald

    def scan_post_image_analysis(runs, runfolder, image_analysis, pathname):
        logging.info("Looking for bustard directories in %s" % (pathname,))
        bustard_glob = os.path.join(pathname, "Bustard*")
        for bustard_pathname in glob(bustard_glob):
            logging.info("Found bustard directory %s" % (bustard_pathname,))
            b = bustard.bustard(bustard_pathname)
            gerald_glob = os.path.join(bustard_pathname, 'GERALD*')
            logging.info("Looking for gerald directories in %s" % (pathname,))
            for gerald_pathname in glob(gerald_glob):
                logging.info("Found gerald directory %s" % (gerald_pathname,))
                try:
                    g = gerald.gerald(gerald_pathname)
                    p = PipelineRun(runfolder)
                    p.image_analysis = image_analysis
                    p.bustard = b
                    p.gerald = g
                    runs.append(p)
                except IOError, e:
                    logging.error("Ignoring " + str(e))

    datadir = os.path.join(runfolder, 'Data')

    logging.info('Searching for runs in ' + datadir)
    runs = []
    # scan for firecrest directories
    for firecrest_pathname in glob(os.path.join(datadir,"*Firecrest*")):
        logging.info('Found firecrest in ' + datadir)
        image_analysis = firecrest.firecrest(firecrest_pathname)
        if image_analysis is None:
	    logging.warn(
                "%s is an empty or invalid firecrest directory" % (firecrest_pathname,)
            )
	else:
            scan_post_image_analysis(
                runs, runfolder, image_analysis, firecrest_pathname
            )
    # scan for IPAR directories
    for ipar_pathname in glob(os.path.join(datadir,"IPAR_*")):
        logging.info('Found ipar directories in ' + datadir)
        image_analysis = ipar.ipar(ipar_pathname)
        if image_analysis is None:
	    logging.warn(
                "%s is an empty or invalid IPAR directory" %(ipar_pathname,)
            )
	else:
            scan_post_image_analysis(
                runs, runfolder, image_analysis, ipar_pathname
            )

    return runs

def get_specific_run(gerald_dir):
    """
    Given a gerald directory, construct a PipelineRun out of its parents

    Basically this allows specifying a particular run instead of the previous
    get_runs which scans a runfolder for various combinations of
    firecrest/ipar/bustard/gerald runs.
    """
    from htsworkflow.pipelines import firecrest
    from htsworkflow.pipelines import ipar
    from htsworkflow.pipelines import bustard
    from htsworkflow.pipelines import gerald

    bustard_dir = os.path.abspath(os.path.join(gerald_dir, '..'))
    image_dir = os.path.abspath(os.path.join(gerald_dir, '..', '..'))

    runfolder_dir = os.path.abspath(os.path.join(image_dir, '..','..'))
   
    logging.debug('--- use-run detected options ---')
    logging.debug('runfolder: %s' % (runfolder_dir,))
    logging.debug('image_dir: %s' % (image_dir,))
    logging.debug('bustard_dir: %s' % (bustard_dir,))
    logging.debug('gerald_dir: %s' % (gerald_dir,))

    # find our processed image dir
    image_run = ipar.ipar(image_dir)
    if image_run is None:
        image_run = firecrest.firecrest(image_dir)
    if image_run is None:
        msg = '%s does not contain an image processing step' % (image_dir,)
        logging.error(msg)
        return None

    # find our base calling
    base_calling_run = bustard.bustard(bustard_dir)
    if base_calling_run is None:
        logging.error('%s does not contain a bustard run' % (bustard_dir,))
        return None

    # find alignments
    gerald_run = gerald.gerald(gerald_dir)
    if gerald_run is None:
        logging.error('%s does not contain a gerald run' % (gerald_dir,))
        return None

    p = PipelineRun(runfolder_dir)
    p.image_analysis = image_run
    p.bustard = base_calling_run
    p.gerald = gerald_run
    
    logging.info('Constructed PipelineRun from %s' % (gerald_dir,))
    return p

def extract_run_parameters(runs):
    """
    Search through runfolder_path for various runs and grab their parameters
    """
    for run in runs:
      run.save()

def summarize_mapped_reads(genome_map, mapped_reads):
    """
    Summarize per chromosome reads into a genome count
    But handle spike-in/contamination symlinks seperately.
    """
    summarized_reads = {}
    genome_reads = 0
    genome = 'unknown'
    for k, v in mapped_reads.items():
        path, k = os.path.split(k)
        if len(path) > 0 and not genome_map.has_key(path):
            genome = path
            genome_reads += v
        else:
            summarized_reads[k] = summarized_reads.setdefault(k, 0) + v
    summarized_reads[genome] = genome_reads
    return summarized_reads

def summarize_lane(gerald, lane_id):
    report = []
    summary_results = gerald.summary.lane_results
    for end in range(len(summary_results)):  
      eland_result = gerald.eland_results.results[end][lane_id]
      report.append("Sample name %s" % (eland_result.sample_name))
      report.append("Lane id %s end %s" % (eland_result.lane_id, end))
      cluster = summary_results[end][eland_result.lane_id].cluster
      report.append("Clusters %d +/- %d" % (cluster[0], cluster[1]))
      report.append("Total Reads: %d" % (eland_result.reads))
      mc = eland_result._match_codes
      nm = mc['NM']
      nm_percent = float(nm)/eland_result.reads  * 100
      qc = mc['QC']
      qc_percent = float(qc)/eland_result.reads * 100

      report.append("No Match: %d (%2.2g %%)" % (nm, nm_percent))
      report.append("QC Failed: %d (%2.2g %%)" % (qc, qc_percent))
      report.append('Unique (0,1,2 mismatches) %d %d %d' % \
                    (mc['U0'], mc['U1'], mc['U2']))
      report.append('Repeat (0,1,2 mismatches) %d %d %d' % \
                    (mc['R0'], mc['R1'], mc['R2']))
      report.append("Mapped Reads")
      mapped_reads = summarize_mapped_reads(eland_result.genome_map, eland_result.mapped_reads)
      for name, counts in mapped_reads.items():
        report.append("  %s: %d" % (name, counts))
      report.append('')
    return report

def summary_report(runs):
    """
    Summarize cluster numbers and mapped read counts for a runfolder
    """
    report = []
    for run in runs:
        # print a run name?
        report.append('Summary for %s' % (run.name,))
	# sort the report
	eland_keys = run.gerald.eland_results.results[0].keys()
	eland_keys.sort(alphanum)

	for lane_id in eland_keys:
            report.extend(summarize_lane(run.gerald, lane_id))
            report.append('---')
            report.append('')
        return os.linesep.join(report)

def is_compressed(filename):
    if os.path.splitext(filename)[1] == ".gz":
        return True
    elif os.path.splitext(filename)[1] == '.bz2':
        return True
    else:
        return False

def extract_results(runs, output_base_dir=None):
    if output_base_dir is None:
        output_base_dir = os.getcwd()

    for r in runs:
      result_dir = os.path.join(output_base_dir, r.flowcell_id)
      logging.info("Using %s as result directory" % (result_dir,))
      if not os.path.exists(result_dir):
        os.mkdir(result_dir)

      # create cycle_dir
      cycle = "C%d-%d" % (r.image_analysis.start, r.image_analysis.stop)
      logging.info("Filling in %s" % (cycle,))
      cycle_dir = os.path.join(result_dir, cycle)
      if os.path.exists(cycle_dir):
        logging.error("%s already exists, not overwriting" % (cycle_dir,))
        continue
      else:
        os.mkdir(cycle_dir)

      # copy stuff out of the main run
      g = r.gerald

      # save run file
      r.save(cycle_dir)

      return

      # Copy Summary.htm
      summary_path = os.path.join(r.gerald.pathname, 'Summary.htm')
      if os.path.exists(summary_path):
          logging.info('Copying %s to %s' % (summary_path, cycle_dir))
          shutil.copy(summary_path, cycle_dir)
      else:
          logging.info('Summary file %s was not found' % (summary_path,))

      # tar score files
      score_files = []

      # check for g.pathname/Temp a new feature of 1.1rc1
      scores_path = g.pathname
      scores_path_temp = os.path.join(scores_path, 'Temp')
      if os.path.isdir(scores_path_temp):
          scores_path = scores_path_temp

      # hopefully we have a directory that contains s_*_score files
      for f in os.listdir(scores_path):
          if re.match('.*_score.txt', f):
              score_files.append(f)

      tar_cmd = ['/bin/tar', 'c'] + score_files
      bzip_cmd = [ 'bzip2', '-9', '-c' ]
      tar_dest_name =os.path.join(cycle_dir, 'scores.tar.bz2')
      tar_dest = open(tar_dest_name, 'w')
      logging.info("Compressing score files from %s" % (scores_path,))
      logging.info("Running tar: " + " ".join(tar_cmd[:10]))
      logging.info("Running bzip2: " + " ".join(bzip_cmd))
      logging.info("Writing to %s" %(tar_dest_name))

      tar = subprocess.Popen(tar_cmd, stdout=subprocess.PIPE, shell=False, 
                             cwd=scores_path)
      bzip = subprocess.Popen(bzip_cmd, stdin=tar.stdout, stdout=tar_dest)
      tar.wait()

      # copy & bzip eland files
      for lanes_dictionary in g.eland_results.results:
          for eland_lane in lanes_dictionary.values():
              source_name = eland_lane.pathname
              path, name = os.path.split(eland_lane.pathname)
              dest_name = os.path.join(cycle_dir, name)
	      logging.info("Saving eland file %s to %s" % \
	                   (source_name, dest_name))

              if is_compressed(name):
                logging.info('Already compressed, Saving to %s' % (dest_name, ))
                shutil.copy(source_name, dest_name)
              else:
                # not compressed
                dest_name += '.bz2'
                args = ['bzip2', '-9', '-c', source_name]
                logging.info('Running: %s' % ( " ".join(args) ))
                bzip_dest = open(dest_name, 'w')
                bzip = subprocess.Popen(args, stdout=bzip_dest)
                logging.info('Saving to %s' % (dest_name, ))
                bzip.wait()

def clean_runs(runs):
    """
    Clean up run folders to optimize for compression.
    """
    # TODO: implement this.
    # rm RunLog*.xml
    # rm pipeline_*.txt
    # rm gclog.txt
    # rm NetCopy.log
    # rm nfn.log
    # rm Images/L*
    # cd Data/C1-*_Firecrest*
    # make clean_intermediate

    pass
