from htsworkflow.frontend.analysis.models import Task, Project
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

class ProjectOptions(admin.ModelAdmin):
  list_display = ('ProjTitle','ProjectTasks')
  list_filter = ()
  search_fieldsets = ['project_name','=tasks__subject1__library_id','=tasks__subject2__library_id','tasks__subject1__library_name','tasks__subject2__library_name','project_notes']
  fieldsets = (
    (None, {
      'fields': (('project_name'),('tasks'),('project_notes'))}),
  )
  filter_horizontal = ('tasks',)

class TaskOptions(admin.ModelAdmin):
  list_display = ('task_name','apply_calc','subject1','subject2','task_params','InProjects','submitted_on','task_status')
  list_filter = ('apply_calc',)
  search_fieldsets = ['task_name','id','=subject1__library_id','=subject2__library_id']
  fieldsets = (
      (None, {
        'fields': (('task_name'),('apply_calc'),('subject1'),('subject2'),('task_params'))
         }),
        ('system fields', {
           'classes': ('collapse',),
         'fields': (('submitted_on'),('task_status','run_note'))
        }),
      )

admin.site.register(Project, ProjectOptions)
admin.site.register(Task, TaskOptions)

