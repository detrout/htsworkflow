from django.http import HttpResponse
from django.shortcuts import render_to_response
from elandifier.eland_config import forms

import os
# Create your views here.


#def contact(request):
#    if request.method == 'POST':
#        form = ContactForm(request.POST)
#        if form.is_valid():
#            # Do form processing here...
#            return HttpResponseRedirect('/url/on_success/')
#    else:
#        form = ContactForm()
#    return


def generateElandConfig(form):
  data = []
  
  form = form.cleaned_data
  
  BASE_DIR = '/data-store01/compbio/genomes'
  
  notes = form['notes'].replace('\r\n', '\n').replace('\r', '\n')
  notes = notes.replace('\n', '\n#  ')
  data.append("# NOTES:")
  data.append("#  %s\n#" % (notes))
  
  #Convert all newline conventions to unix style
  l1d = form['lane1_description'].replace('\r\n', '\n').replace('\r', '\n')
  l2d = form['lane2_description'].replace('\r\n', '\n').replace('\r', '\n')
  l3d = form['lane3_description'].replace('\r\n', '\n').replace('\r', '\n')
  l4d = form['lane4_description'].replace('\r\n', '\n').replace('\r', '\n')
  l5d = form['lane5_description'].replace('\r\n', '\n').replace('\r', '\n')
  l6d = form['lane6_description'].replace('\r\n', '\n').replace('\r', '\n')
  l7d = form['lane7_description'].replace('\r\n', '\n').replace('\r', '\n')
  l8d = form['lane8_description'].replace('\r\n', '\n').replace('\r', '\n')
  
  # Turn new lines into indented commented newlines
  l1d = l1d.replace('\n', '\n#  ')
  l2d = l2d.replace('\n', '\n#  ')
  l3d = l3d.replace('\n', '\n#  ')
  l4d = l4d.replace('\n', '\n#  ')
  l5d = l5d.replace('\n', '\n#  ')
  l6d = l6d.replace('\n', '\n#  ')
  l7d = l7d.replace('\n', '\n#  ')
  l8d = l8d.replace('\n', '\n#  ')
  
  data.append("# Lane1: %s" % (l1d))
  data.append("# Lane2: %s" % (l2d))
  data.append("# Lane3: %s" % (l3d))
  data.append("# Lane4: %s" % (l4d))
  data.append("# Lane5: %s" % (l5d))
  data.append("# Lane6: %s" % (l6d))
  data.append("# Lane7: %s" % (l7d))
  data.append("# Lane8: %s" % (l8d))
  
  #data.append("GENOME_DIR %s" % (BASE_DIR))
  #data.append("CONTAM_DIR %s" % (BASE_DIR))
  read_length = form['read_length']
  data.append("READ_LENGTH %d" % (read_length))
  #data.append("ELAND_REPEAT")
  data.append("ELAND_MULTIPLE_INSTANCES 8")
  
  #Construct genome dictionary to figure out what lanes to put
  # in the config file.
  genome_dict = {}
  l1s = form['lane1_species']
  genome_dict.setdefault(l1s, []).append('1')
  l2s = form['lane2_species']
  genome_dict.setdefault(l2s, []).append('2')
  l3s = form['lane3_species']
  genome_dict.setdefault(l3s, []).append('3')
  l4s = form['lane4_species']
  genome_dict.setdefault(l4s, []).append('4')
  l5s = form['lane5_species']
  genome_dict.setdefault(l5s, []).append('5')
  l6s = form['lane6_species']
  genome_dict.setdefault(l6s, []).append('6')
  l7s = form['lane7_species']
  genome_dict.setdefault(l7s, []).append('7')
  l8s = form['lane8_species']
  genome_dict.setdefault(l8s, []).append('8')
  
  genome_list = genome_dict.keys()
  genome_list.sort()
  
  #Loop through and create entries for each species.
  for genome in genome_list:
    lanes = ''.join(genome_dict[genome])
    data.append('%s:ANALYSIS eland' % (lanes))
    data.append('%s:READ_LENGTH %s' % (lanes, read_length))
    data.append('%s:ELAND_GENOME %s' % (lanes, os.path.join(BASE_DIR, genome)))
    data.append('%s:USE_BASES %s' % (lanes, 'Y'*int(read_length)))
    
  data.append('SEQUENCE_FORMAT --scarf')
  
  return '\n'.join(data)


def index(request):
  """
  """
  if request.method == 'POST':
    form = forms.ConfigForm(request.POST, error_class=forms.DivErrorList)
    if form.is_valid():
      cfg = generateElandConfig(form)
      return HttpResponse(cfg, mimetype="text/plain")
    else:
      return render_to_response('config_form.html', {'form': form })
  
  else:   
    fm = forms.ConfigForm(error_class=forms.DivErrorList)
    return render_to_response('config_form.html', {'form': fm })
