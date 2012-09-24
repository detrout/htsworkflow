# Create your views here.
from datetime import datetime
import os

#from django.template import Context, loader
#shortcut to the above modules
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage, mail_managers
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import get_template

from htsworkflow.frontend.experiments.models import \
     DataRun, \
     DataFile, \
     FlowCell, \
     Lane, \
     Sequencer
from htsworkflow.frontend.experiments.experiments import \
     estimateFlowcellDuration, \
     estimateFlowcellTimeRemaining, \
     roundToDays, \
     getUsersForFlowcell, \
     makeEmailLaneMap

def index(request):
    all_runs = DataRun.objects.order_by('-run_start_time')
    return render_to_response('experiments/index.html',{'data_run_list': all_runs})

def detail(request, run_folder):
    html_str = '<h2>Exp Track Details Page</h2>'
    html_str += 'Run Folder: '+run_folder
    r = get_object_or_404(DataRun,run_folder=run_folder)
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

    send = request.REQUEST.get('send',False)
    if send in ('1', 'on', 'True', 'true', True):
        send = True
    else:
        send = False

    bcc_managers = request.REQUEST.get('bcc', False)
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
            if bcc_managers:
                email.bcc = settings.MANAGERS
            email.bcc = settings.NOTIFICATION_BCC
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
    fc.update_data_runs()


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
    lane.flowcell.update_data_runs()

    dataruns = []
    lane.flowcell.update_data_runs()
    for run in lane.flowcell.datarun_set.all():
        files = run.lane_files().get(lane.lane_number, None)
        dataruns.append((run,
                         lane.lane_number,
                         files))

    context = RequestContext(request,
                             {'lib': lane.library,
                              'lane': lane,
                              'flowcell': lane.flowcell,
                              'filtered_dataruns': dataruns})

    return render_to_response('experiments/flowcell_lane_detail.html',
                              context)

def read_result_file(self, key):
    """Return the contents of filename if everything is approved
    """
    data_file = get_object_or_404(DataFile, random_key = key)

    mimetype = 'application/octet-stream'
    if data_file.file_type.mimetype is not None:
        mimetype = data_file.file_type.mimetype

    if os.path.exists(data_file.pathname):
        return HttpResponse(open(data_file.pathname,'r'),
                            mimetype=mimetype)

    raise Http404


def sequencer(request, sequencer_id):
    sequencer = get_object_or_404(Sequencer, id=sequencer_id)
    context = RequestContext(request,
                             {'sequencer': sequencer})
    return render_to_response('experiments/sequencer.html', context)
