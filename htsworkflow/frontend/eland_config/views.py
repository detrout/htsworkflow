from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist

from htsworkflow.frontend.eland_config import forms
from htsworkflow.frontend.experiments import models

import os
import glob


def _validate_input(data):
  return data.replace('..', '').replace('/', '_').replace('\\', '_')


def getElandConfig(flowcell, regenerate=False):

  if hasattr(settings, 'UPLOADTO_CONFIG_FILE'):
    dest = settings.UPLOADTO_CONFIG_FILE
  else:
    dest = '/tmp'
  file_path = os.path.join(dest, flowcell)

  #If we are regenerating the config file, skip
  # reading of existing file. If the file doesn't
  # exist, try to generate it form the DB.
  if not regenerate and os.path.isfile(file_path):
    f = open(file_path, 'r')
    data = f.read()
    f.close()
    return data

  try:
    fcObj = models.FlowCell.objects.get(flowcell_id__iexact=flowcell)
  except ObjectDoesNotExist:
    return None

  data = []

  #form = form.cleaned_data

  BASE_DIR = '/data-store01/compbio/genomes'

  data.append("# FLOWCELL: %s" % (fcObj.flowcell_id))
  data.append("#")

  notes = fcObj.notes.replace('\r\n', '\n').replace('\r', '\n')
  notes = notes.replace('\n', '\n#  ')
  data.append("# NOTES:")
  data.append("#  %s\n#" % (notes))

  #Convert all newline conventions to unix style
  for lane in fcObj.lane_set.all():
    data.append("# Lane%d: %s | %s" % \
      (lane.lane_number, unicode(lane.library.id),  lane.library.library_name.replace('%', '%%')))

  #data.append("GENOME_DIR %s" % (BASE_DIR))
  #data.append("CONTAM_DIR %s" % (BASE_DIR))
  read_length = fcObj.read_length
  #data.append("ELAND_REPEAT")
  data.append("ELAND_MULTIPLE_INSTANCES 8")

  #Construct genome dictionary to figure out what lanes to put
  # in the config file.
  genome_dict = {}

  #l1s = form['lane1_species']
  for lane in fcObj.lane_set.all():
    species = lane.library.library_species.scientific_name
    genome_dict.setdefault(species, []).append(unicode(lane.lane_number))

  genome_list = genome_dict.keys()
  genome_list.sort()

  #Loop through and create entries for each species.
  for genome in genome_list:
    lanes = ''.join(genome_dict[genome])
    if fcObj.paired_end:
        data.append('%s:ANALYSIS eland_pair' % (lanes))
    else:
        data.append('%s:ANALYSIS eland_extended' % (lanes))
    data.append('%s:READ_LENGTH %s' % (lanes, read_length))
    data.append('%s:ELAND_GENOME %s' % (lanes, '%%(%s)s' % (genome)))
    data.append('%s:USE_BASES %s' % (lanes, 'Y'*int(read_length)))

  data.append('SEQUENCE_FORMAT --fastq')
  data.append('') # want a trailing newline

  data = '\n'.join(data)

  f = open(file_path, 'w')
  f.write(data)
  f.close()

  return data


def config(request, flowcell=None):
  """
  Returns eland config file for a given flowcell number,
  or returns a list of available flowcell numbers.
  """

  # Provide INDEX of available Flowcell config files.
  if flowcell is None:
    #Find all FC* config files and report an index html file
    #fc_list = [ os.path.split(file_path)[1] for file_path in glob.glob(os.path.join(settings.UPLOADTO_CONFIG_FILE, 'FC*')) ]
    fc_list = [ fc.flowcell_id for fc in models.FlowCell.objects.all() ]

    #Convert FC* list to html links
    fc_html = [ '<a href="/eland_config/%s/">%s</a>' % (fc_name, fc_name) for fc_name in fc_list ]

    return HttpResponse('<br />'.join(fc_html))

  #FIXME: Should validate flowcell input before using.
  flowcell = _validate_input(flowcell)
  cfg = getElandConfig(flowcell, regenerate=True)

  if not cfg:
    return HttpResponse("Hmm, config file for %s does not seem to exist." % (flowcell))

  return HttpResponse(cfg, mimetype="text/plain")
