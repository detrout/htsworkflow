#!/usr/bin/env python

from optparse import OptionParser, IndentedHelpFormatter
from ConfigParser import SafeConfigParser

import os
import sys
import urllib

CONFIG_SYSTEM = '/etc/ga_frontend/ga_frontend.conf'
CONFIG_USER = os.path.expanduser('~/.ga_frontend.conf')

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
  if not parser.has_section('server_info'):
    parser.add_section('server_info')
  
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
    if conf_parser.has_option('server_info', 'base_host_url'):
      options.url = conf_parser.get('server_info', 'base_host_url')
  
  print 'URL:', options.url
  print 'OUT:', options.output_filepath
  print ' FC:', options.flowcell
  
  return options


def saveConfigFile(flowcell, base_host_url, output_filepath):
  """
  retrieves the flowcell eland config file, give the base_host_url
  (i.e. http://sub.domain.edu:port)
  """
  url = base_host_url + '/elandifier/config/%s/' % (flowcell)
  
  f = open(output_filepath, 'w')
  web = urllib.urlopen(url)
  f.write(web.read())
  web.close()
  f.close()

if __name__ == '__main__':
  #Display help if no args are presented
  if len(sys.argv) == 1:
    sys.argv.append('-h')
    
  options = getCombinedOptions()
  msg_list = ['ERROR MESSAGES:']
  if options.output_filepath is None:
    msg_list.append("  Output filepath argument required. -o <filepath> or --output=<filepath>")
    
  if options.flowcell is None:
    msg_list.append("  Flow cell argument required. -f <flowcell> or --flowcell=<flowcell>")
    
  if options.url is None:
    msg_list.append("  URL argument required (-u <url> or --url=<url>), or entry\n" \
                    "    in /etc/elandifier/elandifer.conf or ~/.elandifier.conf")
    
  if len(msg_list) > 1:
    print '\n'.join(msg_list)
    sys.exit(0)
  
  saveConfigFile(options.flowcell, options.url, options.output_filepath)
  
