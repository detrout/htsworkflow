from django.conf import settings
from django.http import HttpResponse
from datetime import datetime
from string import *
import re
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import urllib
import urllib2
import os

'''
Example library node from LibraryInfo.xml:
<Library Name="SL14">
<Track Flowcell="FC10135" Lane="4" Filename="071005_FC10135_s4_FoxP2_polyclonal_pfsk1_SL14.align_25.hg18.txt" Count=" 2438679" Complexity="4.51989e-06"/>
<Track Flowcell="FC11977" Lane="6" Filename="070928_FC11977_s6_FoxP2_polyclonal_pfsk1_SL14.align_25.hg18.txt" Count=" 2007880" Complexity="0"/>
<Track Flowcell="FC13593" Lane="5" Filename="071002_FC13593_s5_FoxP2_polyclonal_pfsk1_SL14.align_25.hg18.txt" Count=" 2533720" Complexity="1.97771e-06"/>
</Library>
'''
class LibInfoHandler(ContentHandler):

  def __init__ (self, searchTerm):
    self.searchTerm= searchTerm
    self.currlibid = ''
    self.LanesCount, self.ReadsCount = 0, 0
    self.Msg = 'OK'
       
  def startElement(self, name, attrs):
    try:
      if name == 'Library':     
        self.currlibid = attrs.get('Name',"")      
      elif name == 'Track' and self.searchTerm == self.currlibid:
        self.LanesCount += len(attrs.get('Lane',""))
        self.ReadsCount += int(attrs.get('Count',""))
      #else:
      #  self.Msg += ' | name = '+name+', currlibid = '+ self.currlibid
    except: 
      self.Msg = 'failed parsing xml file'
    return

  #def characters (self, ch):
    # return ..

  #def endElement(self, name):
    # return ..


## TO DO: Change this to read the LibraryInfo.xml only ONCE per ReoprtRequest (do it in the models.py). + Read it directly from the analysis_server

def getLibReads(libid):
  searchTerm= libid
  parser = make_parser()   
  curHandler = LibInfoHandler(searchTerm)
  parser.setContentHandler(curHandler)
  reports_dir = os.path.split(__file__)[0]
  library_info = os.path.join(reports_dir, 'LibraryInfo.xml')
  parser.parse(open(library_info))
  arRes = []
  arRes.append(curHandler.LanesCount) 
  arRes.append(curHandler.ReadsCount)
  arRes.append(curHandler.Msg)

  return arRes

def getWebPage(url,params):
  pdata = urllib.urlencode(params)
  req = urllib2.Request(url,pdata)
  wpage = urllib2.urlopen(req)
  restext = wpage.read()
  wpage.close()
  return restext

def refreshLibInfoFile(request): 
 varStatus = 'getting conf file from exp trac server'
 url = settings.TASKS_PROJS_SERVER+'/LibraryInfo.xml'
 params = {}
 readw = getWebPage(url,params)
 # make sure file content starts as xml
 match_str = re.compile('^<\?xml.+')
 if match_str.search(readw): ##tempstr):
   # Rename current file with timestamp
   year = datetime.today().year.__str__()
   year = replace(year,'20','')
   month = datetime.today().month
   if month < 10: month = "0"+month.__str__()
   else: month = month.__str__()
   day = datetime.today().day
   if day < 10: day = "0"+day.__str__()
   else: day = day.__str__()
   mydate = year+month+day
   folder_loc = '/htsworkflow/htswfrontend/htswfrontend'  # DEV                                                                                                                          
   #folder_loc = '/Library/WebServer/gaworkflow/gaworkflow/frontend'  # PROD
   folder = folder_loc+'/htsw_reports/LibInfo/'
   os.rename(folder+'LibraryInfo.xml',folder+mydate+'_LibraryInfo.xml')
   # create file in curret folder
   file_path = os.path.join(folder,'LibraryInfo.xml')
   f = open(file_path, 'w')
   f.write(readw)
   f.close()
   varStatus = 'OK. LibraryInfo.xml refreshed at Web server.'
 else:
   varStatus = 'Failed reading valid LibraryInfo.xml server reply:\n'+readw
 return HttpResponse(varStatus)  
