#!/usr/bin/env python

from ConfigParser import RawConfigParser
import logging
from optparse import OptionParser, IndentedHelpFormatter
import os
import sys
import urllib
import urllib2

try:
    import json
except ImportError, e:
    import simplejson as json

from htsworkflow.frontend.auth import apidata
from htsworkflow.util.url import normalize_url
from htsworkflow.pipelines.genome_mapper import getAvailableGenomes
from htsworkflow.pipelines.genome_mapper import constructMapperDict

__docformat__ = "restructredtext en"

CONFIG_SYSTEM = '/etc/htsworkflow.ini'
CONFIG_USER = os.path.expanduser('~/.htsworkflow.ini')
GERALD_CONFIG_SECTION = 'gerald_config'

#Disable or enable commandline arg parsing; disabled by default.
DISABLE_CMDLINE = True

LANE_LIST = ['1','2','3','4','5','6','7','8']

class FlowCellNotFound(Exception): pass
class WebError404(Exception): pass

def retrieve_flowcell_info(base_host_url, flowcell):
    """
    Return a dictionary describing a 
    """
    url = base_host_url + '/experiments/config/%s/json' % (flowcell)
  
    try:
        apipayload = urllib.urlencode(apidata)
        web = urllib2.urlopen(url, apipayload)
    except urllib2.URLError, e:
        errmsg = 'URLError: %d %s' % (e.code, e.msg)
        logging.error(errmsg)
        logging.error('opened %s' % (url,))
        raise IOError(errmsg)
    
    contents = web.read()
    headers = web.info()
    
    if web.getcode() == 403:
        msg = "403 - Forbbidden, probably need api key"
        raise FlowCellNotFound(msg)
    
    if web.getcode() == 404:
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
    for lane_number, lane_info in flowcell_info['lane_set'].items():
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
    for lane_number in LANE_LIST:
        lane_info = flowcell_info['lane_set'][lane_number]
        config += ['Lane%s: %s | %s' % (lane_number, lane_info['library_id'],
                                        lane_info['library_name'])]
    config += ['']
    return "\n# ".join(config)

def format_gerald_config(options, flowcell_info, genome_map):
    """
    Generate a GERALD config file
    """
    # so we can add nothing or _pair if we're a paired end run
    run_type_suffix = { False: "", True: "_pair" }

    # it's convienent to have helpful information describing the flowcell
    # in the config file... things like which lane is which library.
    config = [format_gerald_header(flowcell_info)]

    analysis_suffix = run_type_suffix[flowcell_info['paired_end']]
    lane_groups = group_lane_parameters(flowcell_info)
    for lane_index, lane_numbers in lane_groups.items():
        # lane_index is return value of group_lane_parameters
        read_length, species, is_sequencing = lane_index
        lane_numbers.sort()
        lane_prefix = u"".join(lane_numbers)
        
        if not is_sequencing:
            config += ['%s:ANALYSIS eland%s' % (lane_prefix, analysis_suffix)]
        else:
            config += ['%s:ANALYSIS sequence%s' % (lane_prefix, analysis_suffix)]
        #config += ['%s:READ_LENGTH %s' % ( lane_prefix, read_length ) ]
        config += ['%s:USE_BASES Y%s' % ( lane_prefix, read_length ) ]
        species_path = genome_map.get(species, "Unknown")
        config += ['%s:ELAND_GENOME %s' % (lane_prefix, species_path) ]

    # add in option for running script after 
    if options.post_run is not None:
        post_run = options.post_run  % {'runfolder': options.runfolder}
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
    config_host=http://somewhere.domain:port
    genome_dir=/path to search for genomes
    
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
            
    logging.info('USING OPTIONS:')
    logging.info(u'     URL: %s' % (options.url,))
    logging.info(u'     OUT: %s' % (options.output_filepath,))
    logging.info(u'      FC: %s' % (options.flowcell,))
    #logging.info(': %s' % (options.genome_dir,))
    logging.info(u'post_run: %s' % ( unicode(options.post_run),))
    
    return options


def saveConfigFile(options):
  """
  retrieves the flowcell eland config file, give the base_host_url
  (i.e. http://sub.domain.edu:port)
  """
  flowcell_info = retrieve_flowcell_info(options.url, options.flowcell)

  available_genomes = getAvailableGenomes(options.genome_dir)
  genome_map = constructMapperDict(available_genomes)

  config = format_gerald_config(options, flowcell_info, genome_map)

  if options.output_filepath is not None:
      outstream = open(options.output_filepath, 'w')
      logging.info('Writing config file to %s' % (options.output_filepath,))
  else:
      outstream = sys.stdout
      
  outstream.write(config)
  


  
