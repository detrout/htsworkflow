#!/usr/bin/env python

from optparse import OptionParser, IndentedHelpFormatter
from ConfigParser import SafeConfigParser

import os
import sys
import urllib

CONFIG_SYSTEM = '/etc/ga_frontend/ga_frontend.conf'
CONFIG_USER = os.path.expanduser('~/.ga_frontend.conf')


class FlowCellNotFound(Exception): pass
class WebError404(Exception): pass


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

  parser.set_description('Retrieves eland config file from ga_frontend web frontend.')
  
  parser.epilog = """
Config File:
  * %s (System wide)
  * %s (User specific; overrides system)
  * command line overrides all config file options
  
  Example Config File:
  
    [server_info]
    base_host_url=http://somewhere.domain:port
""" % (CONFIG_SYSTEM, CONFIG_USER)
  
  #Special formatter for allowing preformatted description.
  ##parser.format_epilog(PreformattedDescriptionFormatter())

  parser.add_option("-u", "--url",
                    action="store", type="string", dest="url")
  
  parser.add_option("-o", "--output",
                    action="store", type="string", dest="output_filepath")
  
  parser.add_option("-f", "--flowcell",
                    action="store", type="string", dest="flowcell")
  
  #parser.set_default("url", "default")
  
  return parser

def constructConfigParser():
  """
  returns a pre-setup config parser
  """
  parser = SafeConfigParser()
  parser.read([CONFIG_SYSTEM, CONFIG_USER])
  if not parser.has_section('config_file_server'):
    parser.add_section('config_file_server')
  
  return parser


def getCombinedOptions():
  """
  Returns optparse options after it has be updated with ConfigParser
  config files and merged with parsed commandline options.
  """
  cl_parser = constructOptionParser()
  conf_parser = constructConfigParser()
  
  options, args = cl_parser.parse_args()
  
  if options.url is None:
    if conf_parser.has_option('config_file_server', 'base_host_url'):
      options.url = conf_parser.get('config_file_server', 'base_host_url')
  
  print 'USING OPTIONS:'
  print ' URL:', options.url
  print ' OUT:', options.output_filepath
  print '  FC:', options.flowcell
  print ''
  
  return options


def saveConfigFile(flowcell, base_host_url, output_filepath):
  """
  retrieves the flowcell eland config file, give the base_host_url
  (i.e. http://sub.domain.edu:port)
  """
  url = base_host_url + '/eland_config/%s/' % (flowcell)
  
  f = open(output_filepath, 'w')
  #try:
  web = urllib.urlopen(url)
  #except IOError, msg:
  #  if str(msg).find("Connection refused") >= 0:
  #    print 'Error: Connection refused for: %s' % (url)
  #    f.close()
  #    sys.exit(1)
  #  elif str(msg).find("Name or service not known") >= 0:
  #    print 'Error: Invalid domain or ip address for: %s' % (url)
  #    f.close()
  #    sys.exit(2)
  #  else:
  #    raise IOError, msg

  data = web.read()

  if data.find('Hmm, config file for') >= 0:
    msg = "Flowcell (%s) not found in DB; full url(%s)" % (flowcell, url)
    raise FlowCellNotFound, msg

  if data.find('404 - Not Found') >= 0:
    msg = "404 - Not Found: Flowcell (%s); base_host_url (%s);\n full url(%s)\n " \
          "Did you get right port #?" % (flowcell, base_host_url, url)
    raise FlowCellNotFound, msg
  
  f.write(data)
  web.close()
  f.close()
  print 'Wrote config file to %s' % (output_filepath)

  
