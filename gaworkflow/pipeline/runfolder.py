"""
Core information needed to inspect a runfolder.
"""
from glob import glob
import logging
import os
import re
import stat
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

from gaworkflow.util.alphanum import alphanum
from gaworkflow.util.ethelp import indent, flatten


class PipelineRun(object):
    """
    Capture "interesting" information about a pipeline run
    """
    XML_VERSION = 1
    PIPELINE_RUN = 'PipelineRun'
    FLOWCELL_ID = 'FlowcellID'

    def __init__(self, pathname=None, firecrest=None, bustard=None, gerald=None, xml=None):
        self.pathname = pathname
        self._name = None
        self._flowcell_id = None
        self.firecrest = firecrest
        self.bustard = bustard
        self.gerald = gerald

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
	      "Flowcell idwas not found, guessing %s" % (
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
        root.append(self.firecrest.get_elements())
        root.append(self.bustard.get_elements())
        root.append(self.gerald.get_elements())
        return root

    def set_elements(self, tree):
        # this file gets imported by all the others,
        # so we need to hide the imports to avoid a cyclic imports
        from gaworkflow.pipeline import firecrest
        from gaworkflow.pipeline import bustard
        from gaworkflow.pipeline import gerald

        tag = tree.tag.lower()
        if tag != PipelineRun.PIPELINE_RUN.lower():
          raise ValueError('Pipeline Run Expecting %s got %s' % (
              PipelineRun.PIPELINE_RUN, tag))
        for element in tree:
          tag = element.tag.lower()
          if tag == PipelineRun.FLOWCELL_ID.lower():
            self._flowcell_id = element.text
          #ok the xword.Xword.XWORD pattern for module.class.constant is lame
          elif tag == firecrest.Firecrest.FIRECREST.lower():
            self.firecrest = firecrest.Firecrest(xml=element)
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
          tmax = max(self.firecrest.time, self.bustard.time, self.gerald.time)
          timestamp = time.strftime('%Y-%m-%d', time.localtime(tmax))
          self._name = 'run_'+self.flowcell_id+"_"+timestamp+'.xml'
        return self._name
    name = property(_get_run_name)

    def save(self):
        logging.info("Saving run report "+ self.name)
        xml = self.get_elements()
        indent(xml)
        ElementTree.ElementTree(xml).write(self.name)

    def load(self, filename):
        logging.info("Loading run report from " + filename)
        tree = ElementTree.parse(filename).getroot()
        self.set_elements(tree)

def get_runs(runfolder):
    """
    Search through a run folder for all the various sub component runs
    and then return a PipelineRun for each different combination.

    For example if there are two different GERALD runs, this will
    generate two different PipelineRun objects, that differ
    in there gerald component.
    """
    from gaworkflow.pipeline import firecrest
    from gaworkflow.pipeline import bustard
    from gaworkflow.pipeline import gerald

    datadir = os.path.join(runfolder, 'Data')

    logging.info('Searching for runs in ' + datadir)
    runs = []
    for firecrest_pathname in glob(os.path.join(datadir,"*Firecrest*")):
        f = firecrest.firecrest(firecrest_pathname)
        bustard_glob = os.path.join(firecrest_pathname, "Bustard*")
        for bustard_pathname in glob(bustard_glob):
            b = bustard.bustard(bustard_pathname)
            gerald_glob = os.path.join(bustard_pathname, 'GERALD*')
            for gerald_pathname in glob(gerald_glob):
                try:
                    g = gerald.gerald(gerald_pathname)
                    runs.append(PipelineRun(runfolder, f, b, g))
                except IOError, e:
                    print "Ignoring", str(e)
    return runs
                
    
def extract_run_parameters(runs):
    """
    Search through runfolder_path for various runs and grab their parameters
    """
    for run in runs:
      run.save()

def summarize_mapped_reads(mapped_reads):
    """
    Summarize per chromosome reads into a genome count
    But handle spike-in/contamination symlinks seperately.
    """
    summarized_reads = {}
    genome_reads = 0
    genome = 'unknown'
    for k, v in mapped_reads.items():
        path, k = os.path.split(k)
        if len(path) > 0:
            genome = path
            genome_reads += v
        else:
            summarized_reads[k] = summarized_reads.setdefault(k, 0) + v
    summarized_reads[genome] = genome_reads
    return summarized_reads

def summary_report(runs):
    """
    Summarize cluster numbers and mapped read counts for a runfolder
    """
    report = []
    for run in runs:
        # print a run name?
        report.append('Summary for %s' % (run.name,))
	# sort the report
	eland_keys = run.gerald.eland_results.results.keys()
	eland_keys.sort(alphanum)

        lane_results = run.gerald.summary.lane_results
	for lane_id in eland_keys:
	    result = run.gerald.eland_results.results[lane_id]
            report.append("Sample name %s" % (result.sample_name))
            report.append("Lane id %s" % (result.lane_id,))
            cluster = lane_results[result.lane_id].cluster
            report.append("Clusters %d +/- %d" % (cluster[0], cluster[1]))
            report.append("Total Reads: %d" % (result.reads))
            mc = result._match_codes
	    report.append("No Match: %d" % (mc['NM']))
	    report.append("QC Failed: %d" % (mc['QC']))
            report.append('Unique (0,1,2 mismatches) %d %d %d' % \
                          (mc['U0'], mc['U1'], mc['U2']))
            report.append('Repeat (0,1,2 mismatches) %d %d %d' % \
                          (mc['R0'], mc['R1'], mc['R2']))
            report.append("Mapped Reads")
            mapped_reads = summarize_mapped_reads(result.mapped_reads)
            for name, counts in mapped_reads.items():
              report.append("  %s: %d" % (name, counts))
            report.append('---')
            report.append('')
        return os.linesep.join(report)
