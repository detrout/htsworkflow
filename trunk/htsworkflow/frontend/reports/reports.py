from htsworkflow.frontend.experiments.models import *
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render_to_response, get_object_or_404

def getBgColor(reads_cnt,exp_type):
  # Color Scheme: green is more than 12M, blue is more than 5M, orange is more than 3M and red is less. For RNAseq, all those thresholds are ~ double
  bgcolor = '#ff3300'  # Red is the color for minimum read counts                                                                                                                            
  rc_thr = [12000000,5000000,3000000] # Default for ChIP-Seq and Methyl-Seq
  if exp_type == 'RNA-seq':
    rc_thr = [20000000,10000000,6000000]

  if reads_cnt > rc_thr[0]:
    bgcolor = '#66ff66'  # Green                                                                                                                                                                                                                                               
  else:
    if reads_cnt > rc_thr[1]:
      bgcolor ='#00ccff'  # Blue                                                                                                                                                                                                                                               
    else:
       if reads_cnt > rc_thr[2]:
         bgcolor ='#ffcc33'  # Orange                                                                                                                                                                                                                                          
  #tstr = '<div style="background-color:'+bgcolor+';color:black">'
  #tstr += res[0].__str__()+' Lanes, '+rc+' M Reads'
  #tstr += '</div>'

  return bgcolor

def report1(request):
  EXP = 'ChIP-seq'

  if request.GET.has_key('aflid'):
    AFL_Id = request.GET['aflid']
    try:
      AFL = Affiliation.objects.get(id=AFL_Id).name
      AFL_CNT = Affiliation.objects.get(id=AFL_Id).contact
    except ObjectDoesNotExist:
      return HttpResponse("ERROR: Affiliation Record Not Found for: '"+AFL_ID+"'")
  else:
    AFL = 'ENCODE_Tier1'
    AFL_CNT = ''
    try:
      AFL_Id = Affiliation.objects.get(name=AFL,contact=AFL_CNT).id.__str__()
    except ObjectDoesNotExist:
      return HttpResponse("ERROR: Affiliation Record Not Found for: '"+AFL+"'")
  
  TFall = Library.objects.values('antibody').order_by('antibody').distinct()
  CLLall = Library.objects.values('cell_line').order_by('cell_line').distinct()

  TFs = TFall.filter(experiment_type=EXP,affiliations__name=AFL,affiliations__contact=AFL_CNT)
  CLLs = CLLall.filter(experiment_type=EXP,affiliations__name=AFL,affiliations__contact=AFL_CNT)

  # Check Replicate numbers
  Reps = 1
  RepRecs = Library.objects.filter(experiment_type=EXP,affiliations__name=AFL,affiliations__contact=AFL_CNT).order_by('-replicate')
  if len(RepRecs) > 0: Reps = RepRecs[0].replicate
  
  ########
  str = ''
  str += '<span style="margin-right:20px"><a target=_self href="/admin" target=_self">Main Page</a></span>'
  ##str += '<span style="margin-right:20px">Max Replicates: '+MaxRep.replicate.__str__()+'</span>'
  str += '<span>Select another <b>'+EXP+'</b> Report:</span>  <select>'
  for af in Affiliation.objects.distinct():
    str += '<option value='+af.id.__str__()
    if AFL_Id == af.id.__str__():
      str += ' selected'
    str += ' onclick="window.location=\'/reports/report?aflid='+af.id.__str__()+'\'; return false;">'+af.name+' '+af.contact+'</option>'  
  str += '</select>'

  str += '<span style="margin-left:20px;padding:1px;border:solid #cccccc 1px">color scheme: <span style="margin-left:5px;background-color:#66ff66"> > 12 M</span><span style="margin-left:5px;background-color:#00ccff"> >  5 M</span><span style="margin-left:5px;background-color:#ffcc33"> > 3 M</span><span style="margin-left:5px;background-color:#ff3300"> < 3 M</span></span>' 

  str += '<span style="margin-left:20px">'
  str += '<u>Switch to:</u> '+AFL+' '+AFL_CNT+' <a target=_self href="/reports/report_RM?exp=RNA-seq&aflid='+AFL_Id+'"><b>RNA-Seq</b> Report</a>'
  str += '  | '
  str += '<a target=_self href="/reports/report_RM?exp=Methyl-seq&aflid='+AFL_Id+'"><b>Methyl-Seq</b> Report</a>'

  bgc = '#ffffff' 
  pbgc = '#f7f7f7'
  str += '<br/><br/><table border=1 cellspacing="2">'
  str += '<tr><th style="text-align:right">PROJECT</th><th colspan='+(Reps*len(CLLs)).__str__()+' style="text-align:center">'+AFL+' '+AFL_CNT+' <span style="font-size:140%">'+EXP+'</span></th></tr>'
  str += '<tr><th style="text-align:right">CELL LINE</th>'
  for H in CLLs: 
    str += '<th colspan='+Reps.__str__()+' style="text-align:center;background-color:'+bgc+'">'+Cellline.objects.get(id=H['cell_line']).cellline_name+'</th>'
    tbgc = bgc
    bgc = pbgc
    pbgc = tbgc 
  str += '</tr><tr><th style="text-align:left">TF</th>'
  bgc = '#ffffff'
  pbgc = '#f7f7f7'
  for H in CLLs:
    for r in range(1,Reps+1):
      str += '<th style="text-align:center;background-color:'+bgc+'">Rep. '+r.__str__()+'</th>'
    tbgc = bgc
    bgc = pbgc
    pbgc = tbgc
  str += '</tr>'
  str += '<tr><td align=right><a title="View Libraries Records" target=_self href=/admin/fctracker/library/?affiliations__id__exact='+AFL_Id+'&experiment_type__exact=INPUT_RXLCh>Total Chromatin</a></td>'
  bgc = '#ffffff'
  pbgc = '#f7f7f7'
  for H in CLLs:
    for r in range(1,Reps+1):
      repReads = Library.objects.filter(experiment_type='INPUT_RXLCh',affiliations__name=AFL,affiliations__contact=AFL_CNT,cell_line=H['cell_line'].__str__(),replicate=r)
      str += "<td align=center style='background-color:"+bgc+"'>"
      if len(repReads) == 0:
        str += 'No Libraries'
      else:
        cnt = 0
        for R1 in repReads:
          rres = R1.aligned_m_reads()
          # Check data sanlty                                                                                                                                           
          if rres[2] != 'OK':
            str += '<div style="border:solid red 2px">'+rres[2]
          else:
            cnt = rres[1]
            if cnt > 0:
              str += "<div style='background-color:"+getBgColor(cnt,EXP)+";font-size:140%'>"
              str += "%1.2f" % (cnt/1000000.0)+" M"
            else:  str += "<div style='background-color:#ff3300;width:100%;font-size:140%'>0 Reads"
          str += "<div style='font-size:70%'>"+R1.library_id+", "+R1.condition.nickname+"</div>"
          str += "</div>"
      str += '</td>'
    tbgc = bgc
    bgc = pbgc
    pbgc = tbgc
  str += '</tr>' 

  for T in TFs:
    str += '<tr>'
    try:
      if T['antibody']:
        str += '<td><a title="View Libraries Records" target=_self href=/admin/fctracker/library/?affiliations__id__exact='+AFL_Id+'&antibody__id__exact='+T['antibody'].__str__()+'>'+Antibody.objects.get(id=T['antibody']).nickname+'</a></td>'
    except Antibody.DoesNotExist:
      str += '<td>n/a</td>'

    bgc = '#ffffff'
    pbgc = '#f7f7f7'
    for H in CLLs:
      for r in range(1,Reps+1):
        repReads = Library.objects.filter(experiment_type=EXP,affiliations__name=AFL,affiliations__contact=AFL_CNT,cell_line=H['cell_line'].__str__(),antibody=T['antibody'].__str__(),replicate=r)
        str += "<td align=center style='background-color:"+bgc+"'>"
        if len(repReads) == 0: 
          str += 'No Libraries'
        else:
          cnt = 0
          for R1 in repReads:
            rres = R1.aligned_m_reads()
            # Check data sanlty
            if rres[2] != 'OK':
              str += '<div style="border:solid red 2px">'+rres[2]
            else:
              cnt = rres[1]
              if cnt > 0:
                str += "<div style='background-color:"+getBgColor(cnt,EXP)+";font-size:140%'>"
                str += "%1.2f" % (cnt/1000000.0)+" M"
              else:  str += "<div style='background-color:#ff3300;width:100%;font-size:140%'>0 Reads"
            str += "<div style='font-size:70%'>"+R1.library_id+", "+R1.condition.nickname+"</div>"
            str += "</div>"
        str += '</td>'
      tbgc = bgc
      bgc = pbgc
      pbgc = tbgc
    str += '</tr>'
  str += '</table>'

  return render_to_response('reports/report.html',{'main': str})


def report_RM(request): #for RNA-Seq and Methyl-Seq
  EXP = 'RNA-seq'  

  if request.GET.has_key('exp'):
    EXP = request.GET['exp'] # Methyl-seq

  if request.GET.has_key('aflid'):
    AFL_Id = request.GET['aflid']
    try:
      AFL = Affiliation.objects.get(id=AFL_Id).name
      AFL_CNT = Affiliation.objects.get(id=AFL_Id).contact
    except ObjectDoesNotExist:
      return HttpResponse("ERROR: Affiliation Record Not Found for: '"+AFL_ID+"'")
  else:
    AFL = 'ENCODE_Tier1'
    AFL_CNT = ''
    try:
      AFL_Id = Affiliation.objects.get(name=AFL,contact=AFL_CNT).id.__str__()
    except ObjectDoesNotExist:
      return HttpResponse("ERROR: Affiliation Record Not Found for: '"+AFL+"'")

  CLLall = Library.objects.values('cell_line').order_by('cell_line').distinct()
  CLLs = CLLall.filter(experiment_type=EXP,affiliations__name=AFL,affiliations__contact=AFL_CNT)

  ########
  # Check Replicate numbers
  Reps = 1
  RepRecs = Library.objects.filter(experiment_type=EXP,affiliations__name=AFL,affiliations__contact=AFL_CNT).order_by('-replicate')
  if len(RepRecs) > 0: Reps = RepRecs[0].replicate
                                                                                                                                                                              
  str = ''
  str += '<span style="margin-right:20px"><a  target=_self href="/admin" target=_self">Main Page</a></span>'
  str += '<span>Select another <b>'+EXP+'</b> Report:</span> <select>'
  for af in Affiliation.objects.distinct():
    str += '<option value='+af.id.__str__()
    if AFL_Id == af.id.__str__():
      str += ' selected'
    str += ' onclick="window.location=\'/reports/report_RM?exp='+EXP+'&aflid='+af.id.__str__()+'\'; return false;">'+af.name+' '+af.contact+'</option>'
  str += '</select>'

  if EXP == 'RNA-seq':
    str += '<span style="margin-left:20px;padding:1px;border:solid #cccccc 1px">color scheme: <span style="margin-left:5px;background-color:#66ff66"> > 20 M</span><span style="margin-left:5px;background-color:#00ccff"> >  10 M</span><span style="margin-left:5px;background-color:#ffcc33"> > 6 M</span><span style="margin-left:5px;background-color:#ff3300"> < 6 M</span></span>'
    str += '<span style="margin-left:20px">'
    str += '<u>Switch to:</u> '+AFL+' '+AFL_CNT+' <a target=_self href="/reports/report?exp=RNA-seq&aflid='+AFL_Id+'"><b>ChIP-Seq</b> Report</a>'
    str += '  | '
    str += '<a target=_self href="/reports/report_RM?exp=Methyl-seq&aflid='+AFL_Id+'"><b>Methyl-Seq</b> Report</a>'
  else:
    str += '<span style="margin-left:20px;padding:1px;border:solid #cccccc 1px">color scheme: <span style="margin-left:5px;background-color:#66ff66"> > 12 M</span><span style="margin-left:5px;background-color:#00ccff"> >  5 M</span><span style="margin-left:5px;background-color:#ffcc33"> > 3 M</span><span style="margin-left:5px;background-color:#ff3300"> < 3 M</span></span>'
    str += '<span style="margin-left:20px">'
    str += '<u>Switch to:</u> '+AFL+' '+AFL_CNT+' <a target=_self href="/reports/report?exp=RNA-seq&aflid='+AFL_Id+'"><b>ChIP-Seq</b> Report</a>'
    str += '  | '
    str += '<a target=_self href="/reports/report_RM?exp=RNA-seq&aflid='+AFL_Id+'"><b>RNA-Seq</b> Report</a>'

  str += '<br/><br/><table border=1 cellspacing="2">'
  str += '<tr><th colspan='+(Reps*len(CLLs)).__str__()+' style="text-align:center">'+AFL+' '+AFL_CNT+'  <span style="font-size:140%">'+EXP+'</span></th></tr>'
  str += '<tr>'
  bgc = '#ffffff'
  pbgc = '#f7f7f7'
  for H in CLLs:
    str += '<th colspan='+Reps.__str__()+' style="text-align:center;background-color:'+bgc+'">'+Cellline.objects.get(id=H['cell_line']).cellline_name+'</th>'
    tbgc = bgc
    bgc = pbgc
    pbgc = tbgc
  str += '</tr><tr>'
  bgc = '#ffffff'
  pbgc = '#f7f7f7'
  for H in CLLs:
    for r in range(1,Reps+1):
      str += '<th style="text-align:center;background-color:'+bgc+'">Rep. '+r.__str__()+'</th>'
    tbgc = bgc
    bgc = pbgc
    pbgc = tbgc
  str += '</tr>'

  str += '<tr>' 
  bgc = '#ffffff'
  pbgc = '#f7f7f7'
  for H in CLLs:
    for r in range(1,Reps+1):
      repReads = Library.objects.filter(experiment_type=EXP,affiliations__name=AFL,affiliations__contact=AFL_CNT,cell_line=H['cell_line'],replicate=r)                                                                                                                    
      str += "<td align=center valign=top style='background-color:"+bgc+"'>"
      if len(repReads) == 0:
        str += 'No Libraries'
      else:
        cnt = 0
        for R1 in repReads:
          rres = R1.aligned_m_reads()
          # Check data sanlty   
          if rres[2] != 'OK':
            str += '<div style="border:solid red 2px">'+rres[2]
          else:
            cnt = rres[1]
            if cnt > 0:
              str += "<div style='background-color:"+getBgColor(cnt,EXP)+";border:solid #cccccc 1px;font-size:140%'>"
              str += "%1.2f" % (cnt/1000000.0)+" M"
            else:  str += "<div style='background-color:#ff3300;border:solid #cccccc 1px;width:100%;font-size:140%'>0 Reads"
          str += "<div style='font-size:80%'><a title='View Record' target=_self href=/admin/fctracker/library/?q="+R1.library_id+">"+R1.library_id+"</a>, "+R1.condition.nickname+", "+R1.library_species.common_name+"</div>"
          str += "<div style='font-size:70%'>\""+R1.library_name+"\"</div"
          str += "</div>"
      str += '</td>'
    tbgc = bgc
    bgc = pbgc
    pbgc = tbgc
  str += '</tr>'
  str += '</table>'

  return render_to_response('reports/report.html',{'main': str})

def getNotRanFCs(request):
  FCall = FlowCell.objects.order_by('-run_date').distinct()
  str = '<table><tr><th>FlowCell</th><th>Lanes</th><th>Creation Date</th></tr>'
  for f in FCall:
    try:
      t = DataRun.objects.get(fcid=f.id)
    except ObjectDoesNotExist:
      str += '<tr><td>'+f.flowcell_id+'</td><td>'+f.Lanes()+'</td><td>'+f.run_date.__str__()+'</td></tr>'
  str += "</table>"
  return render_to_response('reports/report.html',{'main':str})
 
def test_Libs(request):
  str = ''
  str += '<table border=1><tr><th>Lib ID</th><th>Current Libaray Name (Free Text)</th><th>Auto-composed Libaray Name (antibody + celline + libid + species + [replicate])</th></tr>'
  allLibs = Library.objects.all()
  #allLibs = Library.objects.filter(antibody__isnull=False)
  for L in allLibs:
    str += '<tr>'
    str += '<td>'+L.library_id+'</td><td>'+L.library_name+'</td>'   
    str += '<td>'
    str += L.experiment_type+'_'
    if L.cell_line.cellline_name != 'Unknown':
      str += L.cell_line.cellline_name+'_'

    try:
      if L.antibody is not None:
        str += L.antibody.nickname + '_'
    except Antibody.DoesNotExist:
      pass
  
    str += 'Rep'+L.replicate.__str__()
    str += '</td></tr>' 

  str += '</table>'
  return HttpResponse(str)  
