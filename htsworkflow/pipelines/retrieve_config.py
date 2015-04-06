#!/usr/bin/env python

import csv
from six.moves.configparser import RawConfigParser
import logging
from optparse import OptionParser, IndentedHelpFormatter
import os
import sys
import types
import six
from six.moves import urllib

import json

from htsworkflow.auth import apidata
from htsworkflow.util import api
from htsworkflow.util.alphanum import natural_sort_key
from htsworkflow.util.url import normalize_url
from htsworkflow.pipelines.genome_mapper import \
     getAvailableGenomes, \
     constructMapperDict
from htsworkflow.pipelines import LANE_LIST
# JSON dictionaries use strings
LANE_LIST_JSON = [ str(l) for l in LANE_LIST ]

LOGGER = logging.getLogger(__name__)

__docformat__ = "restructredtext en"

CONFIG_SYSTEM = '/etc/htsworkflow.ini'
CONFIG_USER = os.path.expanduser('~/.htsworkflow.ini')
GERALD_CONFIG_SECTION = 'gerald_config'

#Disable or enable commandline arg parsing; disabled by default.
DISABLE_CMDLINE = True

class FlowCellNotFound(Exception): pass
class WebError404(Exception): pass

def retrieve_flowcell_info(base_host_url, flowcell):
    """
    Return a dictionary describing a
    """
    url = api.flowcell_url(base_host_url, flowcell)

    try:
        apipayload = urllib.parse.urlencode(apidata)
        web = urllib.request.urlopen(url, apipayload)
    except urllib.request.HTTPError as e:
        errmsg = 'URLError: %d %s' % (e.code, e.msg)
        LOGGER.error(errmsg)
        LOGGER.error('opened %s' % (url,))
        raise IOError(errmsg)

    contents = web.read()
    headers = web.info()

    if web.code == 403:
        msg = "403 - Forbbidden, probably need api key"
        raise FlowCellNotFound(msg)

    if web.code == 404:
        msg = "404 - Not Found: Flowcell (%s); base_host_url (%s);\n full url(%s)\n " \
              "Did you get right port #?" % (flowcell, base_host_url, url)
        raise FlowCellNotFound(msg)

    if len(contents) == 0:
        msg = "No information for flowcell (%s) returned; full url(%s)" % (flowcell, url)
        raise FlowCellNotFound(msg)

    data = json.loads(contents)
    return data

def is_sequencing(lane_info):
    """
    Determine if we are just sequencing and not doing any follow-up analysis
    """
    if lane_info['experiment_type'] in ('De Novo','Whole Genome'):
        return True
    else:
        return False

def group_lane_parameters(flowcell_info):
    """
    goup lanes that can share GERALD configuration blocks.

    (The same species, read length, and eland vs sequencing)
    """
    lane_groups = {}
    for lane_number, lane_contents in flowcell_info['lane_set'].items():
        for lane_info in lane_contents:
            index = (lane_info['read_length'],
                     lane_info['library_species'],
                     is_sequencing(lane_info))
            lane_groups.setdefault(index, []).append(lane_number)
    return lane_groups

def format_gerald_header(flowcell_info):
    """
    Generate comment describing the contents of the flowcell
    """
    # I'm using '\n# ' to join the lines together, that doesn't include the
    # first element so i needed to put the # in manually
    config = ['# FLOWCELL: %s' % (flowcell_info['flowcell_id'])]
    config += ['']
    config += ['CONTROL-LANE: %s' % (flowcell_info['control_lane'],)]
    config += ['']
    config += ['Flowcell Notes:']
    config.extend(flowcell_info['notes'].split('\r\n'))
    config += ['']
    for lane_number in sorted(flowcell_info['lane_set']):
        lane_contents = flowcell_info['lane_set'][lane_number]
        for lane_info in lane_contents:
            config += ['Lane%s: %s | %s' % (lane_number,
                                            lane_info['library_id'],
                                            lane_info['library_name'])]

    config += ['']
    return "\n# ".join(config)

def format_gerald_config(options, flowcell_info, genome_map):
    """
    Generate a GERALD config file
    """
    # so we can add nothing or _pair if we're a paired end run
    eland_analysis_suffix = { False: "_extended", True: "_pair" }
    sequence_analysis_suffix = { False: "", True: "_pair" }

    # it's convienent to have helpful information describing the flowcell
    # in the config file... things like which lane is which library.
    config = [format_gerald_header(flowcell_info)]

    config += ['SEQUENCE_FORMAT --fastq']
    config += ['ELAND_SET_SIZE 20']
    config += ['12345678:WITH_SEQUENCE true']
    analysis_suffix = eland_analysis_suffix[flowcell_info['paired_end']]
    sequence_suffix = sequence_analysis_suffix[flowcell_info['paired_end']]
    lane_groups = group_lane_parameters(flowcell_info)
    for lane_index, lane_numbers in lane_groups.items():
        # lane_index is return value of group_lane_parameters
        read_length, species, is_sequencing = lane_index
        lane_numbers.sort()
        lane_prefix = u"".join(lane_numbers)

        species_path = genome_map.get(species, None)
        LOGGER.debug("Looked for genome '%s' got location '%s'" % (species, species_path))
        if not is_sequencing and species_path is None:
            no_genome_msg = "Forcing lanes %s to sequencing as there is no genome for %s"
            LOGGER.warning(no_genome_msg % (lane_numbers, species))
            is_sequencing = True

        if is_sequencing:
            config += ['%s:ANALYSIS sequence%s' % (lane_prefix, sequence_suffix)]
        else:
            config += ['%s:ANALYSIS eland%s' % (lane_prefix, analysis_suffix)]
            config += ['%s:ELAND_GENOME %s' % (lane_prefix, species_path) ]
        #config += ['%s:READ_LENGTH %s' % ( lane_prefix, read_length ) ]
        config += ['%s:USE_BASES Y%s' % ( lane_prefix, read_length ) ]

    # add in option for running script after
    if not (options.post_run is None or options.runfolder is None):
        runfolder = os.path.abspath(options.runfolder)
        post_run = options.post_run  % {'runfolder': runfolder}
        config += ['POST_RUN_COMMAND %s' % (post_run,) ]

    config += [''] # force trailing newline

    return "\n".join(config)

class DummyOptions:
  """
  Used when command line parsing is disabled; default
  """
  def __init__(self):
    self.url = None
    self.output_filepath = None
    self.flowcell = None
    self.genome_dir = None

class PreformattedDescriptionFormatter(IndentedHelpFormatter):

  #def format_description(self, description):
  #
  #  if description:
  #      return description + "\n"
  #  else:
  #     return ""

  def format_epilog(self, epilog):
    """
    It was removing my preformated epilog, so this should override
    that behavior! Muhahaha!
    """
    if epilog:
        return "\n" + epilog + "\n"
    else:
        return ""


def constructOptionParser():
    """
    returns a pre-setup optparser
    """
    parser = OptionParser(formatter=PreformattedDescriptionFormatter())

    parser.set_description('Retrieves eland config file from hts_frontend web frontend.')

    parser.epilog = """
Config File:
  * %s (System wide)
  * %s (User specific; overrides system)
  * command line overrides all config file options

  Example Config File:

    [%s]
    config_host: http://somewhere.domain:port
    genome_dir: /path to search for genomes
    post_run: runfolder -o <destdir> %%(runfolder)s

""" % (CONFIG_SYSTEM, CONFIG_USER, GERALD_CONFIG_SECTION)

    #Special formatter for allowing preformatted description.
    ##parser.format_epilog(PreformattedDescriptionFormatter())

    parser.add_option("-u", "--url",
                      action="store", type="string", dest="url")

    parser.add_option("-o", "--output-file",
                      action="store", type="string", dest="output_filepath",
                      help="config file destination. If runfolder is specified defaults "
                           "to <runfolder>/config-auto.txt" )

    parser.add_option("-f", "--flowcell",
                      action="store", type="string", dest="flowcell")

    parser.add_option("-g", "--genome_dir",
                      action="store", type="string", dest="genome_dir")

    parser.add_option("-r", "--runfolder",
                      action="store", type="string",
                      help="specify runfolder for post_run command ")

    parser.add_option("--sample-sheet", default=None,
                      help="path to save demultiplexing sample sheet")

    parser.add_option("--operator", default='', help="Name of sequencer operator")
    parser.add_option("--recipe", default="Unknown",
                      help="specify recipe name")

    parser.add_option('-v', '--verbose', action='store_true', default=False,
                       help='increase logging verbosity')
    return parser

def constructConfigParser():
    """
    returns a pre-setup config parser
    """
    parser = RawConfigParser()
    parser.read([CONFIG_SYSTEM, CONFIG_USER])
    if not parser.has_section(GERALD_CONFIG_SECTION):
        parser.add_section(GERALD_CONFIG_SECTION)

    return parser


def getCombinedOptions(argv=None):
    """
    Returns optparse options after it has be updated with ConfigParser
    config files and merged with parsed commandline options.

    expects command line arguments to be passed in
    """
    cl_parser = constructOptionParser()
    conf_parser = constructConfigParser()

    if argv is None:
        options = DummyOptions()
    else:
        options, args = cl_parser.parse_args(argv)

    if options.url is None:
        if conf_parser.has_option(GERALD_CONFIG_SECTION, 'config_host'):
            options.url = conf_parser.get(GERALD_CONFIG_SECTION, 'config_host')

    options.url = normalize_url(options.url)

    if options.genome_dir is None:
        if conf_parser.has_option(GERALD_CONFIG_SECTION, 'genome_dir'):
            options.genome_dir = conf_parser.get(GERALD_CONFIG_SECTION, 'genome_dir')

    if conf_parser.has_option(GERALD_CONFIG_SECTION, 'post_run'):
        options.post_run = conf_parser.get(GERALD_CONFIG_SECTION, 'post_run')
    else:
        options.post_run = None

    if options.output_filepath is None:
        if options.runfolder is not None:
            options.output_filepath = os.path.join(options.runfolder, 'config-auto.txt')

    return options


def saveConfigFile(options):
  """
  retrieves the flowcell eland config file, give the base_host_url
  (i.e. http://sub.domain.edu:port)
  """
  LOGGER.info('USING OPTIONS:')
  LOGGER.info(u'     URL: %s' % (options.url,))
  LOGGER.info(u'     OUT: %s' % (options.output_filepath,))
  LOGGER.info(u'      FC: %s' % (options.flowcell,))
  #LOGGER.info(': %s' % (options.genome_dir,))
  LOGGER.info(u'post_run: %s' % ( unicode(options.post_run),))

  flowcell_info = retrieve_flowcell_info(options.url, options.flowcell)

  LOGGER.debug('genome_dir: %s' % ( options.genome_dir, ))
  available_genomes = getAvailableGenomes(options.genome_dir)
  genome_map = constructMapperDict(available_genomes)
  LOGGER.debug('available genomes: %s' % ( unicode( genome_map.keys() ),))

  config = format_gerald_config(options, flowcell_info, genome_map)

  if options.output_filepath is not None:
      outstream = open(options.output_filepath, 'w')
      logging.info('Writing config file to %s' % (options.output_filepath,))
  else:
      outstream = sys.stdout

  outstream.write(config)

  if options.sample_sheet is None:
      pass
  elif options.sample_sheet == '-':
      save_sample_sheet(sys.stdout, options, flowcell_info)
  else:
      stream = open(options.sample_sheet,'w')
      save_sample_sheet(stream, options, flowcell_info)


def save_sample_sheet(outstream, options, flowcell_info):
    sample_sheet_fields = ['FCID', 'Lane', 'SampleID', 'SampleRef', 'Index',
                           'Description', 'Control', 'Recipe', 'Operator',
                           'SampleProject']
    illumina_to_htsw_map = {'FCID': 'flowcell',
                            'Lane': 'lane_number',
                            'SampleID': 'library_id',
                            'SampleRef': format_sampleref,
                            'Description': 'library_name',
                            'Control': format_control_lane,
                            'Recipe': format_recipe_name,
                            'Operator': format_operator_name}
    out = csv.DictWriter(outstream, sample_sheet_fields)
    out.writerow(dict(((x,x) for x in sample_sheet_fields)))
    for lane_number in sorted(flowcell_info['lane_set']):
        lane_contents = flowcell_info['lane_set'][lane_number]

        pooled_lane_contents = []
        for library in lane_contents:
            # build common attributes
            renamed = {}
            for illumina_name in sample_sheet_fields:
                htsw_field = illumina_to_htsw_map.get(illumina_name, None)
                if htsw_field is None:
                    continue
                if callable(htsw_field):
                    renamed[illumina_name] = htsw_field(options,
                                                        flowcell_info,
                                                        library)
                else:
                    renamed[illumina_name] = library[htsw_field]

            pooled_lane_contents.extend(format_pooled_libraries(renamed, library))

        for row in pooled_lane_contents:
            out.writerow(row)


def format_sampleref(options, flowcell_info, sample):
    return sample['library_species'].replace(' ', '_')


def format_control_lane(options, flowcell_info, sample):
    if sample['lane_number'] == flowcell_info['control_lane']:
        return 'Y'
    else:
        return 'N'


def format_recipe_name(options, flowcell_info, sample):
    return options.recipe


def format_operator_name(options, flowcell_info, sample):
    return options.operator


def format_pooled_libraries(shared, library):
    sequences = library.get('index_sequence', None)
    if sequences is None:
        return []
    elif isinstance(sequences, six.string_types):
        shared['Index'] = ''
        shared['SampleProject'] = library['library_id']
        return [shared]
    elif isinstance(sequences, dict):
        pooled = []
        multiplex_ids = sorted(sequences.keys(), key=natural_sort_key)
        for multiplex_id in multiplex_ids:
            sample = {}
            sample.update(shared)
            sample['Index'] = sequences[multiplex_id]
            sample['SampleProject'] = format_project_name(library,
                                                          multiplex_id)
            pooled.append(sample)
        return pooled
    else:
        raise RuntimeError("Unrecognized index type")



def format_project_name(library, multiplex_id):
    library_id = library['library_id']
    return "%s_index%s" % (library_id, multiplex_id)


