# Create your views here.
from django.http import HttpResponse
from django.shortcuts import get_list_or_404
from gaworkflow.frontend.fctracker.models import Library, Person

def labindex(request):
	return HttpResponse("Testing this page")

def labdetail(request, lab_name):
	members = get_list_or_404(Person, lab=lab_name)
	lab_libraries = Library.objects.filter(made_for__in=members)
	output = ', '.join([q.library_name for q in lab_libraries])
	return HttpResponse(output)
