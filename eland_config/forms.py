from __future__ import unicode_literals

from django import forms
from django.forms.util import ErrorList


SPECIES_LIST = [#('--choose--', '--Choose--'),
                ('hg18', 'Homo sapiens (Hg18)'),
                ('Mm8', 'Mus musculus (Mm8)'),
                ('arabv6', 'Arabadopsis Thaliana v6'),
                ('other', 'Other species (Include in description)')]


class DivErrorList(ErrorList):
  def __unicode__(self):
    return self.as_divs()
  
  def as_divs(self):
    if not self: return u''
    return u'<div class="errorlist">%s</div>' % (''.join([u'<div class="error">%s</div>' % e for e in self]))



class ConfigForm(forms.Form):
  
  flow_cell_number = forms.CharField(min_length=2)
  run_date = forms.DateTimeField()
  advanced_run = forms.BooleanField(required=False)
  read_length = forms.IntegerField(min_value=1, initial=32)
  #eland_repeat = forms.BooleanField()
  
  #needs a for loop or something to allow for n configurations
  #analysis_type = forms.ChoiceField(choices=[('eland','eland')])
  lane1_species = forms.ChoiceField(choices=SPECIES_LIST)
  lane1_description = forms.CharField(widget=forms.TextInput(attrs={'size':'60'}))
  
  lane2_species = forms.ChoiceField(choices=SPECIES_LIST)
  lane2_description = forms.CharField(widget=forms.TextInput(attrs={'size':'60'}))
  
  lane3_species = forms.ChoiceField(choices=SPECIES_LIST)
  lane3_description = forms.CharField(widget=forms.TextInput(attrs={'size':'60'}))
  
  lane4_species = forms.ChoiceField(choices=SPECIES_LIST)
  lane4_description = forms.CharField(widget=forms.TextInput(attrs={'size':'60'}))
  
  lane5_species = forms.ChoiceField(choices=SPECIES_LIST)
  lane5_description = forms.CharField(widget=forms.TextInput(attrs={'size':'60'}))
  
  lane6_species = forms.ChoiceField(choices=SPECIES_LIST)
  lane6_description = forms.CharField(widget=forms.TextInput(attrs={'size':'60'}))
  
  lane7_species = forms.ChoiceField(choices=SPECIES_LIST)
  lane7_description = forms.CharField(widget=forms.TextInput(attrs={'size':'60'}))
  
  lane8_species = forms.ChoiceField(choices=SPECIES_LIST)
  lane8_description = forms.CharField(widget=forms.TextInput(attrs={'size':'60'}))
  
  notes = forms.CharField(widget=forms.Textarea(attrs={'cols':'70'}), required=False)
  
  #lane_specific_read_length = forms.IntegerField(min_value=1)
  
  #eland_genome_lanes = forms.MultipleChoiceField(choices=[('lane1','1'),
  #                                              ('lane2','2'),
  #                                              ('lane3','3'),
  #                                              ('lane4','4'),
  #                                              ('lane5','5'),
  #                                              ('lane6','6'),
  #                                              ('lane7','7'),
  #                                              ('lane8','8') ])
  
  #eland_genome = forms.ChoiceField(choices=)
  
  #use_bases_lanes = forms.MultipleChoiceField(choices=[('lane1','1'),
  #                                              ('lane2','2'),
  #                                              ('lane3','3'),
  #                                              ('lane4','4'),
  #                                              ('lane5','5'),
  #                                              ('lane6','6'),
  #                                              ('lane7','7'),
  #                                              ('lane8','8') ])
  
  #use_bases_mask = forms.CharField()
  
  #sequence_format = forms.ChoiceField(choices=[('scarf', 'scarf')])
  
  
  
  #subject = forms.CharField(max_length=100)
  #message = forms.CharField()
  #sender = forms.EmailField()
  #cc_myself = forms.BooleanField()
  
  def as_custom(self):
    """
    Displays customized html output
    """
    html = []
    
    fcn = self['flow_cell_number']
    
    html.append(fcn.label_tag() + ': ' + str(fcn) + str(fcn.errors) + '<br />')
    
    run_date = self['run_date']
    html.append(run_date.label_tag() + ': ' + str(run_date) + str(run_date.errors) + '<br />')
    
    arun = self['advanced_run']
    html.append(arun.label_tag() + ': ' + str(arun) + str(arun.errors) + '<br />')
    
    rl = self['read_length']
    html.append(rl.label_tag() + ': ' + str(rl) + str(rl.errors) + '<br /><br />')
    
    html.append('<table border="0">')
    html.append(' <tr><td>%s</td><td>%s</td><td>%s</td></tr>' \
                % ('Lane', 'Species', 'Description'))
    
    l1s = self['lane1_species']
    l1d = self['lane1_description']
    html.append(' <tr><td>%s</td><td>%s %s</td><td>%s %s</td></tr>' \
                % ('1', str(l1s), str(l1s.errors), str(l1d), str(l1d.errors)))
    
    l2s = self['lane2_species']
    l2d = self['lane2_description']
    html.append(' <tr><td>%s</td><td>%s %s</td><td>%s %s</td></tr>' \
                % ('2', str(l2s), str(l2s.errors), str(l2d), str(l2d.errors)))
    
    l3s = self['lane3_species']
    l3d = self['lane3_description']
    html.append(' <tr><td>%s</td><td>%s %s</td><td>%s %s</td></tr>' \
                % ('3', str(l3s), str(l3s.errors), str(l3d), str(l3d.errors)))
    
    l4s = self['lane4_species']
    l4d = self['lane4_description']
    html.append(' <tr><td>%s</td><td>%s %s</td><td>%s %s</td></tr>' \
                % ('4', str(l4s), str(l4s.errors), str(l4d), str(l4d.errors)))
    
    l5s = self['lane5_species']
    l5d = self['lane5_description']
    html.append(' <tr><td>%s</td><td>%s %s</td><td>%s %s</td></tr>' \
                % ('5', str(l5s), str(l5s.errors), str(l5d), str(l5d.errors)))
    
    l6s = self['lane6_species']
    l6d = self['lane6_description']
    html.append(' <tr><td>%s</td><td>%s %s</td><td>%s %s</td></tr>' \
                % ('6', str(l6s), str(l6s.errors), str(l6d), str(l6d.errors)))
    
    l7s = self['lane7_species']
    l7d = self['lane7_description']
    html.append(' <tr><td>%s</td><td>%s %s</td><td>%s %s</td></tr>' \
                % ('7', str(l7s), str(l7s.errors), str(l7d), str(l7d.errors)))
    
    l8s = self['lane8_species']
    l8d = self['lane8_description']
    html.append(' <tr><td>%s</td><td>%s %s</td><td>%s %s</td></tr>' \
                % ('8', str(l8s), str(l8s.errors), str(l8d), str(l8d.errors)))
    
    html.append('</table><br />')
    
    notes = self['notes']
    html.append('<p>Notes:</p>')
    html.append(' %s<br />' % (str(notes)))
    
    return '\n'.join(html)
    
    
    
