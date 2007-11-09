#!/usr/bin/env python

from optparse import OptionParser
from ConfigParser import SafeConfigParser

import os
import sys
import urllib


def constructOptionParser():
  parser = OptionParser()
  
  parser.add_option("-u", "--url",
                    action="store", type="string", dest="url")
  
  parser.add_option("-o", "--output",
                    action="store", type="string", dest="output_filepath")
  
  parser.add_option("-f", "--flowcell",
                    action="store", type="string", dest="flowcell")
  
  #parser.set_default("url", "default")
  
  return parser

def constructConfigParser():
  parser = SafeConfigParser()
  parser.read(['/etc/elandifier/elandifier.conf',
               os.path.expanduser('~/.elandifier.conf')])
  if not parser.has_section('server_info'):
    parser.add_section('server_info')
  
  return parser


def getCombinedOptions():
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
  
