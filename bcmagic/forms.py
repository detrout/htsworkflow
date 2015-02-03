from __future__ import unicode_literals

from django import forms

class BarcodeMagicForm(forms.Form):
    magic = forms.CharField(label="Barcode Magic", required=False)
    bcm_mode = forms.CharField(widget=forms.HiddenInput, initial="default")
    
    class Media:
        js = ('js/jquery.timers-1.0.0.js',
              'js/bcmagic-ext.js')
