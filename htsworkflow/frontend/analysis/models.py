from django.db import models
from datetime import datetime
from htswfrontend.fctracker.models import Library 
from string import *

class Task(models.Model):
  task_name = models.CharField(max_length=50,unique=True, db_index=True)
  subject1 = models.ForeignKey(Library,related_name='sbj1_library',verbose_name="Subject")
  subject2 = models.ForeignKey(Library,related_name='sbj2_library',verbose_name="Subject 2 / Control",blank=True,null=True)
  CALCS = (
      ('QuEST', 'QuEST Peak Calling'),
      ('WingPeaks', 'Wing Peak Calling'),
      ('MACS', 'MACS Peak Calling'),
      ('qPCR', 'In Silico qPCR'),
      ('CompareLibs', 'Compare Libaraies'),
      ('ComparePeakCalls','Compare Peak Calls'),
      ('ProfileReads','Profile Reads')
    )
  apply_calc = models.CharField(max_length=50,choices=CALCS,verbose_name='Applied Calculation')
  ## userid = # logged in user
  task_status = models.CharField(max_length=500,blank=True,null=True,default='defined')
  results_location = models.CharField(max_length=2000,blank=True,null=True) 
  submitted_on = models.DateTimeField(core=True,default=datetime.now())
  run_note = models.CharField(max_length=500,blank=True,null=True)
  
  def __str__(self):
      return '"%s" - %s on [%s]/[%s]' % (self.task_name,self.apply_calc,self.subject1,self.subject2)

  def InProjects(self):
      return '...'
      ps = self.project_set.all()
      pstr = 'In '
      return pstr
      for p in ps:
        pstr += '%s, ' % (p.project_name) 
      return pstr

  class Admin:
    list_display = ('task_name','apply_calc','subject1','subject2','InProjects','submitted_on','task_status')
    list_filter = ('apply_calc',)
    search_fields = ['task_name','id','=subject1__library_id','=subject2__library_id']
    fields = (
        (None, {
          'fields': (('task_name'),('apply_calc'),('subject1'),('subject2'))
           }),
          ('system fields', {
             'classes': 'collapse',
           'fields': (('submitted_on'),('task_status','run_note'))
          }),
        )
    
    
class Project(models.Model):
    project_name = models.CharField(max_length=50,unique=True, db_index=True)
    tasks = models.ManyToManyField(Task,related_name='project_tasks',null=True,filter_interface=models.HORIZONTAL)
    project_notes = models.CharField(max_length=500,blank=True,null=True)
    
    def __str__(self):
      return '%s' % (self.project_name)

    def ProjectTasks(self):
      ptasks = self.tasks.all().order_by('id')
      surl = 'http://m304-apple-server.stanford.edu/projects/' 
      tstr = '<script>'
      tstr += 'function togView(eid){'
      tstr += 'f=document.getElementById(eid);'
      tstr += 'if(f.height==0){'
      tstr += 'f.height=600;'
      tstr += 'f.style.border=\'solid #cccccc 3px\';'
      tstr += '}else{'
      tstr += 'f.height=0;'
      tstr += 'f.style.border=\'none\';'
      tstr += '}'
      tstr += '}'
      tstr += '</script>'
      Style = ''
      if len(ptasks) > 8:  Style = ' style="height:200px;overflow:auto" '
      tstr += '<div '+Style+'>'
      tstr += '<table><tr><th>Tasks</th><th>Job Status</th>'
      isregistered = False
      for t in ptasks:
        tstr += '<tr><td width=250>%s</td><td>%s</td></tr>'  % (t.task_name,replace(t.task_status,'Complete','<span style="color:green;font-weight:bolder">Complete</span>'))
        if t.task_status != 'defined': isregistered = True

      tstr += '</table>'
      tstr += '</div>' 
      tstr += '<div>'
      tstr += '<div align=center>'
      if isregistered:
        tstr += '<a onClick="togView(\'RFrame'+self.id.__str__()+'\');" href="'+surl+self.id.__str__()+'/" title="View Results Page" target="RFrame'+self.id.__str__()+'">VIEW PROJECT RESULTS</a>'
        tstr += '<a href="'+surl+self.id.__str__()+'/" title="View Results Page" target="_blank" style="margin-left:10px">(view in new window)</a>'
      else:
        tstr += 'REGISTERING ...'    
 
      tstr += '</div>'    
      tstr += '<iframe width="100%" height="0" frameborder="0" style="background-color:#ffffff" name="RFrame'+self.id.__str__()+'" id="RFrame'+self.id.__str__()+'"/></iframe>'
      tstr += '</div>'
      return tstr

    ProjectTasks.allow_tags = True

    def ProjTitle(self):
      ptasks = self.tasks.all().order_by('id')
      tasks_counter = '<span style="color:#666666;font-size:85%">('+len(ptasks).__str__() + ' tasks)</span>'
      htmlstr = '%s<br/>%s'  % (self.project_name,tasks_counter)
      return htmlstr

    ProjTitle.allow_tags = True

    class Admin:
      list_display = ('ProjTitle','ProjectTasks')
      list_filter = ()
      search_fields = ['project_name','=tasks__subject1__library_id','=tasks__subject2__library_id','tasks__subject1__library_name','tasks__subject2__library_name','project_notes']
      fields = (
        (None, {
          'fields': (('project_name'),('tasks'),('project_notes'))}),
        )
