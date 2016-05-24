from __future__ import absolute_import, print_function, unicode_literals

# Create your views here.
from datetime import datetime
import os

#from django.template import Context, loader
#shortcut to the above modules
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.http import HttpResponse, Http404
from django.shortcuts import render, render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import get_template

from .models import SequencingRun, DataFile, FlowCell, Lane, Sequencer
from .admin import LaneOptions
from .experiments import estimateFlowcellTimeRemaining, roundToDays, \
     getUsersForFlowcell, \
     makeEmailLaneMap
from samples.changelist import HTSChangeList
from samples.models import HTSUser


def index(request):
    all_runs = SequencingRun.objects.order_by('-run_start_time')
    return render_to_response('experiments/index.html',{'data_run_list': all_runs})

def detail(request, run_folder):
    html_str = '<h2>Exp Track Details Page</h2>'
    html_str += 'Run Folder: '+run_folder
    r = get_object_or_404(SequencingRun,run_folder=run_folder)
    return render_to_response('experiments/detail.html',{'run_f': r})

def makeFCSheet(request,fcid):
  # get Flowcell by input fcid
  # ...
  rec = None
  try:
    rec = FlowCell.objects.get(flowcell_id=fcid)
  except ObjectDoesNotExist:
    pass
  lanes = ['1','2','3','4','5','6','7','8']
  return render_to_response('experiments/flowcellSheet.html',{'fc': rec})


@user_passes_test(lambda u: u.is_staff)
def startedEmail(request, pk):
    """
    Create the we have started processing your samples email
    """
    fc = get_object_or_404(FlowCell, id=pk)

    send = request.GET.get('send',False)
    if send in ('1', 'on', 'True', 'true', True):
        send = True
    else:
        send = False

    bcc_managers = request.GET.get('bcc', False)
    if bcc_managers in ('on', '1', 'True', 'true'):
        bcc_managers = True
    else:
        bcc_managers = False

    email_lane = makeEmailLaneMap(fc)
    flowcell_users = getUsersForFlowcell(fc)
    estimate = estimateFlowcellTimeRemaining(fc)
    estimate_low, estimate_high = roundToDays(estimate)
    email_verify = get_template('experiments/email_preview.html')
    email_template = get_template('experiments/started_email.txt')
    sender = settings.NOTIFICATION_SENDER

    warnings = []
    emails = []

    emailless_users = []
    for user in flowcell_users:
        # provide warning
        if user.email is None or len(user.email) == 0:
            warnings.append((user.admin_url(), user.username))
    user=None

    for user_email in email_lane.keys():
        sending = ""
        # build body
        context = RequestContext(request,
                                 {u'flowcell': fc,
                                  u'lanes': email_lane[user_email],
                                  u'runfolder': 'blank',
                                  u'finish_low': estimate_low,
                                  u'finish_high': estimate_high,
                                  u'now': datetime.now(),
                                  })

        # build view
        subject = "Flowcell %s" % ( fc.flowcell_id )
        body = email_template.render(context)

        if send:
            email = EmailMessage(subject, body, sender, to=[user_email])
            notified = set()
            if bcc_managers:
                for manager in settings.MANAGERS:
                    if len(manager) > 0:
                        notified.add(manager)
            for user in settings.NOTIFICATION_BCC:
                if len(user) > 0:
                    notified.add(user)
            email.bcc = list(notified)
            email.send()

        emails.append((user_email, subject, body, sending))

    verify_context = RequestContext(
        request,
        { 'emails': emails,
          'flowcell': fc,
          'from': sender,
          'send': send,
          'site_managers': settings.MANAGERS,
          'title': fc.flowcell_id,
          'warnings': warnings,
        })
    return HttpResponse(email_verify.render(verify_context))

def finishedEmail(request, pk):
    """
    """
    return HttpResponse("I've got nothing.")


def flowcell_detail(request, flowcell_id, lane_number=None):
    fc = get_object_or_404(FlowCell, flowcell_id__startswith=flowcell_id)
    fc.update_sequencing_runs()

    if lane_number is not None:
        lanes = fc.lane_set.filter(lane_number=lane_number)
    else:
        lanes = fc.lane_set.all()

    context = RequestContext(request,
                             {'flowcell': fc,
                              'lanes': lanes})

    return render_to_response('experiments/flowcell_detail.html',
                              context)

def flowcell_lane_detail(request, lane_pk):
    lane = get_object_or_404(Lane, id=lane_pk)
    lane.flowcell.update_sequencing_runs()

    sequencingruns = []
    lane.flowcell.update_sequencing_runs()
    for run in lane.flowcell.sequencingrun_set.all():
        files = run.lane_files().get(lane.lane_number, None)
        sequencingruns.append((run,
                         lane.lane_number,
                         files))

    context = RequestContext(request,
                             {'lib': lane.library,
                              'lane': lane,
                              'flowcell': lane.flowcell,
                              'filtered_sequencingruns': sequencingruns})

    return render_to_response('experiments/flowcell_lane_detail.html',
                              context)

def read_result_file(self, key):
    """Return the contents of filename if everything is approved
    """
    data_file = get_object_or_404(DataFile, random_key = key)

    content_type = 'application/octet-stream'
    if data_file.file_type.mimetype is not None:
        content_type = data_file.file_type.mimetype

    if os.path.exists(data_file.pathname):
        return HttpResponse(open(data_file.pathname,'rb'),
                            content_type=content_type)

    raise Http404


def sequencer(request, sequencer_id):
    sequencer = get_object_or_404(Sequencer, id=sequencer_id)
    context = RequestContext(request,
                             {'sequencer': sequencer})
    return render_to_response('experiments/sequencer.html', context)


def lanes_for(request, username=None):
    """
    Generate a report of recent activity for a user
    """
    query = {}
    if username is not None:
        try:
            user = HTSUser.objects.get(username=username)
            query.update({'library__affiliations__users__id': user.id})
        except HTSUser.DoesNotExist as e:
            raise Http404('User not found')

    fcl = HTSChangeList(request, Lane,
                        list_filter=['library__affiliations',
                                     'library__library_species'],
                        search_fields=['flowcell__flowcell_id', 'library__id', 'library__library_name'],
                        list_per_page=200,
                        model_admin=LaneOptions(Lane, None),
                        extra_filters=query
                        )

    context = {'lanes': fcl, 'title': 'Lane Index'}

    return render_to_response(
        'samples/lanes_for.html',
        context,
        context_instance=RequestContext(request)
    )
