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
import tarfile
import time

import lxml.etree as ElementTree

LOGGER = logging.getLogger(__name__)

EUROPEAN_STRPTIME = "%d-%m-%Y"
EUROPEAN_DATE_RE = "([0-9]{1,2}-[0-9]{1,2}-[0-9]{4,4})"
VERSION_RE = "([0-9\.]+)"
USER_RE = "([a-zA-Z0-9]+)"
LANES_PER_FLOWCELL = 8
LANE_LIST = range(1, LANES_PER_FLOWCELL + 1)

from htsworkflow.util.alphanum import alphanum
from htsworkflow.util.ethelp import indent, flatten
from htsworkflow.util.queuecommands import QueueCommands

from htsworkflow.pipelines import srf

class PipelineRun(object):
    """
    Capture "interesting" information about a pipeline run
    """
    XML_VERSION = 1
    PIPELINE_RUN = 'PipelineRun'
    FLOWCELL_ID = 'FlowcellID'

    def __init__(self, pathname=None, flowcell_id=None, xml=None):
        if pathname is not None:
          self.pathname = os.path.normpath(pathname)
        else:
          self.pathname = None
        self._name = None
        self._flowcell_id = flowcell_id
        self.datadir = None
        self.image_analysis = None
        self.bustard = None
        self.gerald = None

        if xml is not None:
          self.set_elements(xml)

    def _get_flowcell_id(self):
        # extract flowcell ID
        if self._flowcell_id is None:
            self._flowcell_id = self._get_flowcell_id_from_runinfo()
        if self._flowcell_id is None:
            self._flowcell_id = self._get_flowcell_id_from_flowcellid()
        if self._flowcell_id is None:
            self._flowcell_id = self._get_flowcell_id_from_path()
        if self._flowcell_id is None:
            self._flowcell_id = 'unknown'

            LOGGER.warning(
                "Flowcell id was not found, guessing %s" % (
                    self._flowcell_id))

        return self._flowcell_id
    flowcell_id = property(_get_flowcell_id)

    def _get_flowcell_id_from_flowcellid(self):
        """Extract flowcell id from a Config/FlowcellId.xml file
        """
        config_dir = os.path.join(self.pathname, 'Config')
        flowcell_id_path = os.path.join(config_dir, 'FlowcellId.xml')
        if os.path.exists(flowcell_id_path):
            flowcell_id_tree = ElementTree.parse(flowcell_id_path)
            return flowcell_id_tree.findtext('Text')

    def _get_flowcell_id_from_runinfo(self):
        """Read RunInfo file for flowcell id
        """
        runinfo = os.path.join(self.pathname, 'RunInfo.xml')
        if os.path.exists(runinfo):
            tree = ElementTree.parse(runinfo)
            root = tree.getroot()
            fc_nodes = root.xpath('/RunInfo/Run/Flowcell')
            if len(fc_nodes) == 1:
                return fc_nodes[0].text


    def _get_flowcell_id_from_path(self):
        """Guess a flowcell name from the path
        """
        path_fields = self.pathname.split('_')
        if len(path_fields) > 0:
            # guessing last element of filename
            return path_fields[-1]

    def _get_runfolder_name(self):
        if self.gerald is None:
            return None
        else:
            return self.gerald.runfolder_name
    runfolder_name = property(_get_runfolder_name)

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
          elif tag == gerald.CASAVA.GERALD.lower():
            self.gerald = gerald.CASAVA(xml=element)
          else:
            LOGGER.warn('PipelineRun unrecognized tag %s' % (tag,))

    def _get_run_name(self):
        """
        Given a run tuple, find the latest date and use that as our name
        """
        if self._name is None:
          tmax = max(self.image_analysis.time, self.bustard.time, self.gerald.time)
          timestamp = time.strftime('%Y-%m-%d', time.localtime(tmax))
          self._name = 'run_' + self.flowcell_id + "_" + timestamp + '.xml'
        return self._name
    name = property(_get_run_name)

    def save(self, destdir=None):
        if destdir is None:
            destdir = ''
        LOGGER.info("Saving run report " + self.name)
        xml = self.get_elements()
        indent(xml)
        dest_pathname = os.path.join(destdir, self.name)
        ElementTree.ElementTree(xml).write(dest_pathname)

    def load(self, filename):
        LOGGER.info("Loading run report from " + filename)
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

def get_runs(runfolder, flowcell_id=None):
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

    def scan_post_image_analysis(runs, runfolder, datadir, image_analysis, pathname):
        LOGGER.info("Looking for bustard directories in %s" % (pathname,))
        bustard_dirs = glob(os.path.join(pathname, "Bustard*"))
        # RTA BaseCalls looks enough like Bustard.
        bustard_dirs.extend(glob(os.path.join(pathname, "BaseCalls")))
        for bustard_pathname in bustard_dirs:
            LOGGER.info("Found bustard directory %s" % (bustard_pathname,))
            b = bustard.bustard(bustard_pathname)
            build_gerald_runs(runs, b, image_analysis, bustard_pathname, datadir, pathname, runfolder)

            build_aligned_runs(image_analysis, runs, b, datadir, runfolder)

    def build_gerald_runs(runs, b, image_analysis, bustard_pathname, datadir, pathname, runfolder):
        gerald_glob = os.path.join(bustard_pathname, 'GERALD*')
        LOGGER.info("Looking for gerald directories in %s" % (pathname,))
        for gerald_pathname in glob(gerald_glob):
            LOGGER.info("Found gerald directory %s" % (gerald_pathname,))
            try:
                g = gerald.gerald(gerald_pathname)
                p = PipelineRun(runfolder, flowcell_id)
                p.datadir = datadir
                p.image_analysis = image_analysis
                p.bustard = b
                p.gerald = g
                runs.append(p)
            except IOError, e:
                LOGGER.error("Ignoring " + str(e))


    def build_aligned_runs(image_analysis, runs, b, datadir, runfolder):
        aligned_glob = os.path.join(runfolder, 'Aligned*')
        for aligned in glob(aligned_glob):
            LOGGER.info("Found aligned directory %s" % (aligned,))
            try:
                g = gerald.gerald(aligned)
                p = PipelineRun(runfolder, flowcell_id)
                p.datadir = datadir
                p.image_analysis = image_analysis
                p.bustard = b
                p.gerald = g
                runs.append(p)
            except IOError, e:
                LOGGER.error("Ignoring " + str(e))

    datadir = os.path.join(runfolder, 'Data')

    LOGGER.info('Searching for runs in ' + datadir)
    runs = []
    # scan for firecrest directories
    for firecrest_pathname in glob(os.path.join(datadir, "*Firecrest*")):
        LOGGER.info('Found firecrest in ' + datadir)
        image_analysis = firecrest.firecrest(firecrest_pathname)
        if image_analysis is None:
            LOGGER.warn(
                "%s is an empty or invalid firecrest directory" % (firecrest_pathname,)
            )
        else:
            scan_post_image_analysis(
                runs, runfolder, datadir, image_analysis, firecrest_pathname
            )
    # scan for IPAR directories
    ipar_dirs = glob(os.path.join(datadir, "IPAR_*"))
    # The Intensities directory from the RTA software looks a lot like IPAR
    ipar_dirs.extend(glob(os.path.join(datadir, 'Intensities')))
    for ipar_pathname in ipar_dirs:
        LOGGER.info('Found ipar directories in ' + datadir)
        image_analysis = ipar.ipar(ipar_pathname)
        if image_analysis is None:
            LOGGER.warn(
                "%s is an empty or invalid IPAR directory" % (ipar_pathname,)
            )
        else:
            scan_post_image_analysis(
                runs, runfolder, datadir, image_analysis, ipar_pathname
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

    gerald_dir = os.path.expanduser(gerald_dir)
    bustard_dir = os.path.abspath(os.path.join(gerald_dir, '..'))
    image_dir = os.path.abspath(os.path.join(gerald_dir, '..', '..'))

    runfolder_dir = os.path.abspath(os.path.join(image_dir, '..', '..'))

    LOGGER.info('--- use-run detected options ---')
    LOGGER.info('runfolder: %s' % (runfolder_dir,))
    LOGGER.info('image_dir: %s' % (image_dir,))
    LOGGER.info('bustard_dir: %s' % (bustard_dir,))
    LOGGER.info('gerald_dir: %s' % (gerald_dir,))

    # find our processed image dir
    image_run = None
    # split into parent, and leaf directory
    # leaf directory should be an IPAR or firecrest directory
    data_dir, short_image_dir = os.path.split(image_dir)
    LOGGER.info('data_dir: %s' % (data_dir,))
    LOGGER.info('short_iamge_dir: %s' % (short_image_dir,))

    # guess which type of image processing directory we have by looking
    # in the leaf directory name
    if re.search('Firecrest', short_image_dir, re.IGNORECASE) is not None:
        image_run = firecrest.firecrest(image_dir)
    elif re.search('IPAR', short_image_dir, re.IGNORECASE) is not None:
        image_run = ipar.ipar(image_dir)
    elif re.search('Intensities', short_image_dir, re.IGNORECASE) is not None:
        image_run = ipar.ipar(image_dir)

    # if we din't find a run, report the error and return
    if image_run is None:
        msg = '%s does not contain an image processing step' % (image_dir,)
        LOGGER.error(msg)
        return None

    # find our base calling
    base_calling_run = bustard.bustard(bustard_dir)
    if base_calling_run is None:
        LOGGER.error('%s does not contain a bustard run' % (bustard_dir,))
        return None

    # find alignments
    gerald_run = gerald.gerald(gerald_dir)
    if gerald_run is None:
        LOGGER.error('%s does not contain a gerald run' % (gerald_dir,))
        return None

    p = PipelineRun(runfolder_dir)
    p.image_analysis = image_run
    p.bustard = base_calling_run
    p.gerald = gerald_run

    LOGGER.info('Constructed PipelineRun from %s' % (gerald_dir,))
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
        if len(path) > 0 and path not in genome_map:
            genome = path
            genome_reads += v
        else:
            summarized_reads[k] = summarized_reads.setdefault(k, 0) + v
    summarized_reads[genome] = genome_reads
    return summarized_reads

def summarize_lane(gerald, lane_id):
    report = []
    lane_results = gerald.summary.lane_results
    eland_result = gerald.eland_results[lane_id]
    report.append("Sample name %s" % (eland_result.sample_name))
    report.append("Lane id %s end %s" % (lane_id.lane, lane_id.read))

    if lane_id.read < len(lane_results) and \
           lane_id.lane in lane_results[lane_id.read]:
        summary_results = lane_results[lane_id.read][lane_id.lane]
        cluster = summary_results.cluster
        report.append("Clusters %d +/- %d" % (cluster[0], cluster[1]))
    report.append("Total Reads: %d" % (eland_result.reads))

    if hasattr(eland_result, 'match_codes'):
        mc = eland_result.match_codes
        nm = mc['NM']
        nm_percent = float(nm) / eland_result.reads * 100
        qc = mc['QC']
        qc_percent = float(qc) / eland_result.reads * 100

        report.append("No Match: %d (%2.2g %%)" % (nm, nm_percent))
        report.append("QC Failed: %d (%2.2g %%)" % (qc, qc_percent))
        report.append('Unique (0,1,2 mismatches) %d %d %d' % \
                      (mc['U0'], mc['U1'], mc['U2']))
        report.append('Repeat (0,1,2 mismatches) %d %d %d' % \
                      (mc['R0'], mc['R1'], mc['R2']))

    if hasattr(eland_result, 'genome_map'):
        report.append("Mapped Reads")
        mapped_reads = summarize_mapped_reads(eland_result.genome_map,
                                              eland_result.mapped_reads)
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
	eland_keys = sorted(run.gerald.eland_results.keys())
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

def save_flowcell_reports(data_dir, cycle_dir):
    """
    Save the flowcell quality reports
    """
    data_dir = os.path.abspath(data_dir)
    status_file = os.path.join(data_dir, 'Status.xml')
    reports_dir = os.path.join(data_dir, 'reports')
    reports_dest = os.path.join(cycle_dir, 'flowcell-reports.tar.bz2')
    if os.path.exists(reports_dir):
        cmd_list = [ 'tar', 'cjvf', reports_dest, 'reports/' ]
        if os.path.exists(status_file):
            cmd_list.extend(['Status.xml', 'Status.xsl'])
        LOGGER.info("Saving reports from " + reports_dir)
        cwd = os.getcwd()
        os.chdir(data_dir)
        q = QueueCommands([" ".join(cmd_list)])
        q.run()
        os.chdir(cwd)


def save_summary_file(pipeline, cycle_dir):
    # Copy Summary.htm
    gerald_object = pipeline.gerald
    gerald_summary = os.path.join(gerald_object.pathname, 'Summary.htm')
    status_files_summary = os.path.join(pipeline.datadir, 'Status_Files', 'Summary.htm')
    if os.path.exists(gerald_summary):
        LOGGER.info('Copying %s to %s' % (gerald_summary, cycle_dir))
        shutil.copy(gerald_summary, cycle_dir)
    elif os.path.exists(status_files_summary):
        LOGGER.info('Copying %s to %s' % (status_files_summary, cycle_dir))
        shutil.copy(status_files_summary, cycle_dir)
    else:
        LOGGER.info('Summary file %s was not found' % (summary_path,))

def save_ivc_plot(bustard_object, cycle_dir):
    """
    Save the IVC page and its supporting images
    """
    plot_html = os.path.join(bustard_object.pathname, 'IVC.htm')
    plot_image_path = os.path.join(bustard_object.pathname, 'Plots')
    plot_images = os.path.join(plot_image_path, 's_?_[a-z]*.png')

    plot_target_path = os.path.join(cycle_dir, 'Plots')

    if os.path.exists(plot_html):
        LOGGER.debug("Saving %s" % (plot_html,))
        LOGGER.debug("Saving %s" % (plot_images,))
        shutil.copy(plot_html, cycle_dir)
        if not os.path.exists(plot_target_path):
            os.mkdir(plot_target_path)
        for plot_file in glob(plot_images):
            shutil.copy(plot_file, plot_target_path)
    else:
        LOGGER.warning('Missing IVC.html file, not archiving')


def compress_score_files(bustard_object, cycle_dir):
    """
    Compress score files into our result directory
    """
    # check for g.pathname/Temp a new feature of 1.1rc1
    scores_path = bustard_object.pathname
    scores_path_temp = os.path.join(scores_path, 'Temp')
    if os.path.isdir(scores_path_temp):
        scores_path = scores_path_temp

    # hopefully we have a directory that contains s_*_score files
    score_files = []
    for f in os.listdir(scores_path):
        if re.match('.*_score.txt', f):
            score_files.append(f)

    tar_cmd = ['tar', 'c'] + score_files
    bzip_cmd = [ 'bzip2', '-9', '-c' ]
    tar_dest_name = os.path.join(cycle_dir, 'scores.tar.bz2')
    tar_dest = open(tar_dest_name, 'w')
    LOGGER.info("Compressing score files from %s" % (scores_path,))
    LOGGER.info("Running tar: " + " ".join(tar_cmd[:10]))
    LOGGER.info("Running bzip2: " + " ".join(bzip_cmd))
    LOGGER.info("Writing to %s" % (tar_dest_name,))

    env = {'BZIP': '-9'}
    tar = subprocess.Popen(tar_cmd, stdout=subprocess.PIPE, shell=False, env=env,
                           cwd=scores_path)
    bzip = subprocess.Popen(bzip_cmd, stdin=tar.stdout, stdout=tar_dest)
    tar.wait()


def compress_eland_results(gerald_object, cycle_dir, num_jobs=1):
    """
    Compress eland result files into the archive directory
    """
    # copy & bzip eland files
    bz_commands = []

    for key in gerald_object.eland_results:
        eland_lane = gerald_object.eland_results[key]
        for source_name in eland_lane.pathnames:
            if source_name is None:
              LOGGER.info(
                "Lane ID %s does not have a filename." % (eland_lane.lane_id,))
            else:
              path, name = os.path.split(source_name)
              dest_name = os.path.join(cycle_dir, name)
              LOGGER.info("Saving eland file %s to %s" % \
                         (source_name, dest_name))

              if is_compressed(name):
                LOGGER.info('Already compressed, Saving to %s' % (dest_name,))
                shutil.copy(source_name, dest_name)
              else:
                # not compressed
                dest_name += '.bz2'
                args = ['bzip2', '-9', '-c', source_name, '>', dest_name ]
                bz_commands.append(" ".join(args))
                #LOGGER.info('Running: %s' % ( " ".join(args) ))
                #bzip_dest = open(dest_name, 'w')
                #bzip = subprocess.Popen(args, stdout=bzip_dest)
                #LOGGER.info('Saving to %s' % (dest_name, ))
                #bzip.wait()

    if len(bz_commands) > 0:
      q = QueueCommands(bz_commands, num_jobs)
      q.run()


def extract_results(runs, output_base_dir=None, site="individual", num_jobs=1, raw_format='qseq'):
    """
    Iterate over runfolders in runs extracting the most useful information.
      * run parameters (in run-*.xml)
      * eland_result files
      * score files
      * Summary.htm
      * srf files (raw sequence & qualities)
    """
    if output_base_dir is None:
        output_base_dir = os.getcwd()

    for r in runs:
      result_dir = os.path.join(output_base_dir, r.flowcell_id)
      LOGGER.info("Using %s as result directory" % (result_dir,))
      if not os.path.exists(result_dir):
        os.mkdir(result_dir)

      # create cycle_dir
      cycle = "C%d-%d" % (r.image_analysis.start, r.image_analysis.stop)
      LOGGER.info("Filling in %s" % (cycle,))
      cycle_dir = os.path.join(result_dir, cycle)
      cycle_dir = os.path.abspath(cycle_dir)
      if os.path.exists(cycle_dir):
        LOGGER.error("%s already exists, not overwriting" % (cycle_dir,))
        continue
      else:
        os.mkdir(cycle_dir)

      # save run file
      r.save(cycle_dir)

      # save illumina flowcell status report
      save_flowcell_reports(os.path.join(r.image_analysis.pathname, '..'), cycle_dir)

      # save stuff from bustard
      # grab IVC plot
      save_ivc_plot(r.bustard, cycle_dir)

      # build base call saving commands
      if site is not None:
        lanes = []
        for lane in range(1, 9):
          lane_parameters = r.gerald.lanes.get(lane, None)
          if lane_parameters is not None and lane_parameters.analysis != 'none':
            lanes.append(lane)

        run_name = srf.pathname_to_run_name(r.pathname)
        seq_cmds = []
        LOGGER.info("Raw Format is: %s" % (raw_format, ))
        if raw_format == 'fastq':
            rawpath = os.path.join(r.pathname, r.gerald.runfolder_name)
            LOGGER.info("raw data = %s" % (rawpath,))
            srf.copy_hiseq_project_fastqs(run_name, rawpath, site, cycle_dir)
        elif raw_format == 'qseq':
            seq_cmds = srf.make_qseq_commands(run_name, r.bustard.pathname, lanes, site, cycle_dir)
        elif raw_format == 'srf':
            seq_cmds = srf.make_srf_commands(run_name, r.bustard.pathname, lanes, site, cycle_dir, 0)
        else:
            raise ValueError('Unknown --raw-format=%s' % (raw_format))
        srf.run_commands(r.bustard.pathname, seq_cmds, num_jobs)

      # save stuff from GERALD
      # copy stuff out of the main run
      g = r.gerald

      # save summary file
      save_summary_file(r, cycle_dir)

      # compress eland result files
      compress_eland_results(g, cycle_dir, num_jobs)

      # md5 all the compressed files once we're done
      md5_commands = srf.make_md5_commands(cycle_dir)
      srf.run_commands(cycle_dir, md5_commands, num_jobs)

def rm_list(files, dry_run=True):
    for f in files:
        if os.path.exists(f):
            LOGGER.info('deleting %s' % (f,))
            if not dry_run:
                if os.path.isdir(f):
                    shutil.rmtree(f)
                else:
                    os.unlink(f)
        else:
            LOGGER.warn("%s doesn't exist." % (f,))

def clean_runs(runs, dry_run=True):
    """
    Clean up run folders to optimize for compression.
    """
    if dry_run:
        LOGGER.info('In dry-run mode')

    for run in runs:
        LOGGER.info('Cleaninging %s' % (run.pathname,))
        # rm RunLog*.xml
        runlogs = glob(os.path.join(run.pathname, 'RunLog*xml'))
        rm_list(runlogs, dry_run)
        # rm pipeline_*.txt
        pipeline_logs = glob(os.path.join(run.pathname, 'pipeline*.txt'))
        rm_list(pipeline_logs, dry_run)
        # rm gclog.txt?
        # rm NetCopy.log? Isn't this robocopy?
        logs = glob(os.path.join(run.pathname, '*.log'))
        rm_list(logs, dry_run)
        # rm nfn.log?
        # Calibration
        calibration_dir = glob(os.path.join(run.pathname, 'Calibration_*'))
        rm_list(calibration_dir, dry_run)
        # rm Images/L*
        LOGGER.info("Cleaning images")
        image_dirs = glob(os.path.join(run.pathname, 'Images', 'L*'))
        rm_list(image_dirs, dry_run)
        # rm ReadPrep
        LOGGER.info("Cleaning ReadPrep*")
        read_prep_dirs = glob(os.path.join(run.pathname, 'ReadPrep*'))
        rm_list(read_prep_dirs, dry_run)
        # rm ReadPrep
        LOGGER.info("Cleaning Thubmnail_images")
        thumbnail_dirs = glob(os.path.join(run.pathname, 'Thumbnail_Images'))
        rm_list(thumbnail_dirs, dry_run)

        # make clean_intermediate
        logging.info("Cleaning intermediate files")
        if os.path.exists(os.path.join(run.image_analysis.pathname, 'Makefile')):
            clean_process = subprocess.Popen(['make', 'clean_intermediate'],
                                             cwd=run.image_analysis.pathname,)
            clean_process.wait()



