import time
import threading

######################
# Utility functions
def _percentCompleted(completed, total):
  """
  Returns precent completed as float
  """
  return (completed / float(total)) * 100


##################################################
# Functions to be called by Thread(target=<func>)
def _cmdLineStatusMonitorFunc(conf_info):
  """
  Given a ConfigInfo object, provides status to stdout.

  You should probably use startCmdLineStatusMonitor()
  instead of ths function.

  Use with:
    t = threading.Thread(target=_cmdLineStatusMonitorFunc,
                         args=[conf_info])
    t.setDaemon(True)
    t.start()
  """
  SLEEP_AMOUNT = 30

  while 1:
    if conf_info.status is None:
      print "No status object yet."
      time.sleep(SLEEP_AMOUNT)
      continue
    
    fc, ft = conf_info.status.statusFirecrest()
    bc, bt = conf_info.status.statusBustard()
    gc, gt = conf_info.status.statusGerald()
    tc, tt = conf_info.status.statusTotal()
    
    fp = _percentCompleted(fc, ft)
    bp = _percentCompleted(bc, bt)
    gp = _percentCompleted(gc, gt)
    tp = _percentCompleted(tc, tt)
    
    print 'Firecrest: %s%% (%s/%s)' % (fp, fc, ft)
    print '  Bustard: %s%% (%s/%s)' % (bp, bc, bt)
    print '   Gerald: %s%% (%s/%s)' % (gp, gc, gt)
    print '-----------------------'
    print '    Total: %s%% (%s/%s)' % (tp, tc, tt)
    print ''

    time.sleep(SLEEP_AMOUNT)


#############################################
# Start monitor thread convenience functions
def startCmdLineStatusMonitor(conf_info):
  """
  Starts a command line status monitor given a conf_info object.
  """
  t = threading.Thread(target=_cmdLineStatusMonitorFunc, args=[conf_info])
  t.setDaemon(True)
  t.start()
