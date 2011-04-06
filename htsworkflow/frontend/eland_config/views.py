from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist

from htsworkflow.frontend.eland_config import forms
from htsworkflow.frontend.experiments import models

import os
import glob
# Create your views here.


def _validate_input(data):
  #if data.find('..') == -1 or data.find('/') == -1 or data.find('\\') == -1:
  return data.replace('..', '').replace('/', '_').replace('\\', '_')

#def contact(request):
#    if request.method == 'POST':
#        form = ContactForm(request.POST)
#        if form.is_valid():
#            # Do form processing here...
#            return HttpResponseRedirect('/url/on_success/')
#    else:
#        form = ContactForm()
#    return



#def _saveConfigFile(form):
#  """
#  Given a valid form, save eland config to file based on flowcell number.
#  """
#  assert form.is_valid()
#  
#  clean_data = form.cleaned_data
#  flowcell = clean_data['flow_cell_number'].replace('/','_').replace('..', '__')
#  
#  file_path = os.path.join(settings.UPLOADTO_CONFIG_FILE, flowcell)
#  
#  f = open(file_path, 'w')
#  cfg = generateElandConfig(form)
#  f.write(cfg)
#  f.close()
#  
#
#def _saveToDb(form):
#  """
#  Save info to the database.
#  """
#  clean_data = form.cleaned_data
#  
#  fc_id = clean_data['flow_cell_number']
#  
#  try:
#    fc = models.FlowCell.objects.get(flowcell_id=fc_id)
#  except models.FlowCell.DoesNotExist:
#    fc = models.FlowCell()
#    
#  fc.flowcell_id = fc_id
#  fc.run_date = clean_data['run_date']
#  
#  #LANE 1
#  fc.lane1_sample = clean_data['lane1_description']
#  species_name = clean_data['lane1_species']
#  try:
#    specie = models.Specie.objects.get(scientific_name=species_name)
#  except models.Specie.DoesNotExist:
#    specie = models.Specie(scientific_name=species_name)
#    specie.save()
#  fc.lane1_species = specie
#  
#  #LANE 2
#  fc.lane2_sample = clean_data['lane2_description']
#  species_name = clean_data['lane2_species']
#  try:
#    specie = models.Specie.objects.get(scientific_name=species_name)
#  except models.Specie.DoesNotExist:
#    specie = models.Specie(scientific_name=species_name)
#    specie.save()
#  fc.lane2_species = specie
#  
#  #LANE 3
#  fc.lane3_sample = clean_data['lane3_description']
#  species_name = clean_data['lane3_species']
#  try:
#    specie = models.Specie.objects.get(scientific_name=species_name)
#  except models.Specie.DoesNotExist:
#    specie = models.Specie(scientific_name=species_name)
#    specie.save()
#  fc.lane3_species = specie
#  
#  #LANE 4
#  fc.lane4_sample = clean_data['lane4_description']
#  species_name = clean_data['lane4_species']
#  try:
#    specie = models.Specie.objects.get(scientific_name=species_name)
#  except models.Specie.DoesNotExist:
#    specie = models.Specie(scientific_name=species_name)
#    specie.save()
#  fc.lane4_species = specie
#  
#  #LANE 5
#  fc.lane5_sample = clean_data['lane5_description']
#  species_name = clean_data['lane5_species']
#  try:
#    specie = models.Specie.objects.get(scientific_name=species_name)
#  except models.Specie.DoesNotExist:
#    specie = models.Specie(scientific_name=species_name)
#    specie.save()
#  fc.lane5_species = specie
#  
#  #LANE 6
#  fc.lane6_sample = clean_data['lane6_description']
#  species_name = clean_data['lane6_species']
#  try:
#    specie = models.Specie.objects.get(scientific_name=species_name)
#  except models.Specie.DoesNotExist:
#    specie = models.Specie(scientific_name=species_name)
#    specie.save()
#  fc.lane6_species = specie
#  
#  #LANE 7
#  fc.lane7_sample = clean_data['lane7_description']
#  species_name = clean_data['lane7_species']
#  try:
#    specie = models.Specie.objects.get(scientific_name=species_name)
#  except models.Specie.DoesNotExist:
#    specie = models.Specie(scientific_name=species_name)
#    specie.save()
#  fc.lane7_species = specie
#  
#  #LANE 8
#  fc.lane8_sample = clean_data['lane8_description']
#  species_name = clean_data['lane8_species']
#  try:
#    specie = models.Specie.objects.get(scientific_name=species_name)
#  except models.Specie.DoesNotExist:
#    specie = models.Specie(scientific_name=species_name)
#    specie.save()
#  fc.lane8_species = specie
#  
#  fc.notes = clean_data['notes']
#  
#  fc.save()
#  
#  return fc
#  
#
#def generateElandConfig(form):
#  data = []
#  
#  form = form.cleaned_data
#  
#  BASE_DIR = '/data-store01/compbio/genomes'
#  
#  data.append("# FLOWCELL: %s" % (form['flow_cell_number']))
#  data.append("#")
#  
#  notes = form['notes'].replace('\r\n', '\n').replace('\r', '\n')
#  notes = notes.replace('\n', '\n#  ')
#  data.append("# NOTES:")
#  data.append("#  %s\n#" % (notes))
#  
#  #Convert all newline conventions to unix style
#  l1d = form['lane1_description'].replace('\r\n', '\n').replace('\r', '\n')
#  l2d = form['lane2_description'].replace('\r\n', '\n').replace('\r', '\n')
#  l3d = form['lane3_description'].replace('\r\n', '\n').replace('\r', '\n')
#  l4d = form['lane4_description'].replace('\r\n', '\n').replace('\r', '\n')
#  l5d = form['lane5_description'].replace('\r\n', '\n').replace('\r', '\n')
#  l6d = form['lane6_description'].replace('\r\n', '\n').replace('\r', '\n')
#  l7d = form['lane7_description'].replace('\r\n', '\n').replace('\r', '\n')
#  l8d = form['lane8_description'].replace('\r\n', '\n').replace('\r', '\n')
#  
#  # Turn new lines into indented commented newlines
#  l1d = l1d.replace('\n', '\n#  ')
#  l2d = l2d.replace('\n', '\n#  ')
#  l3d = l3d.replace('\n', '\n#  ')
#  l4d = l4d.replace('\n', '\n#  ')
#  l5d = l5d.replace('\n', '\n#  ')
#  l6d = l6d.replace('\n', '\n#  ')
#  l7d = l7d.replace('\n', '\n#  ')
#  l8d = l8d.replace('\n', '\n#  ')
#  
#  data.append("# Lane1: %s" % (l1d))
#  data.append("# Lane2: %s" % (l2d))
#  data.append("# Lane3: %s" % (l3d))
#  data.append("# Lane4: %s" % (l4d))
#  data.append("# Lane5: %s" % (l5d))
#  data.append("# Lane6: %s" % (l6d))
#  data.append("# Lane7: %s" % (l7d))
#  data.append("# Lane8: %s" % (l8d))
#  
#  #data.append("GENOME_DIR %s" % (BASE_DIR))
#  #data.append("CONTAM_DIR %s" % (BASE_DIR))
#  read_length = form['read_length']
#  data.append("READ_LENGTH %d" % (read_length))
#  #data.append("ELAND_REPEAT")
#  data.append("ELAND_MULTIPLE_INSTANCES 8")
#  
#  #Construct genome dictionary to figure out what lanes to put
#  # in the config file.
#  genome_dict = {}
#  l1s = form['lane1_species']
#  genome_dict.setdefault(l1s, []).append('1')
#  l2s = form['lane2_species']
#  genome_dict.setdefault(l2s, []).append('2')
#  l3s = form['lane3_species']
#  genome_dict.setdefault(l3s, []).append('3')
#  l4s = form['lane4_species']
#  genome_dict.setdefault(l4s, []).append('4')
#  l5s = form['lane5_species']
#  genome_dict.setdefault(l5s, []).append('5')
#  l6s = form['lane6_species']
#  genome_dict.setdefault(l6s, []).append('6')
#  l7s = form['lane7_species']
#  genome_dict.setdefault(l7s, []).append('7')
#  l8s = form['lane8_species']
#  genome_dict.setdefault(l8s, []).append('8')
#  
#  genome_list = genome_dict.keys()
#  genome_list.sort()
#  
#  #Loop through and create entries for each species.
#  for genome in genome_list:
#    lanes = ''.join(genome_dict[genome])
#    data.append('%s:ANALYSIS eland' % (lanes))
#    data.append('%s:READ_LENGTH %s' % (lanes, read_length))
#    data.append('%s:ELAND_GENOME %s' % (lanes, os.path.join(BASE_DIR, genome)))
#    data.append('%s:USE_BASES %s' % (lanes, 'Y'*int(read_length)))
#    
#  data.append('SEQUENCE_FORMAT --scarf')
#  
#  return '\n'.join(data)


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




#def index(request):
#  """
#  Return a form for filling out information about the flowcell
#  """
#  if request.method == 'POST':
#    form = forms.ConfigForm(request.POST, error_class=forms.DivErrorList)
#    if form.is_valid():
#      #cfg = generateElandConfig(form)
#      _saveConfigFile(form)
#      _saveToDb(form)
#      return HttpResponse("Eland Config Saved!", mimetype="text/plain")
#    else:
#      return render_to_response('config_form.html', {'form': form })
#  
#  else:   
#    fm = forms.ConfigForm(error_class=forms.DivErrorList)
#    return render_to_response('config_form.html', {'form': fm })
