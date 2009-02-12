__docformat__ = "restructuredtext en"

import glob
import re
import os
import sys
import time
import threading

s_comment = re.compile('^#')
s_general_read_len = re.compile('^READ_LENGTH ')
s_read_len = re.compile('^[1-8]+:READ_LENGTH ')

s_firecrest = None

# FIRECREST PATTERNS
# _p2f(<pattern>, lane, tile, cycle)
PATTERN_FIRECREST_QCM = 's_%s_%s_%s_qcm.xml'

# _p2f(<pattern>, lane, tile)
PATTERN_FIRECREST_INT = 's_%s_%s_02_int.txt'
PATTERN_FIRECREST_NSE = 's_%s_%s_nse.txt.gz'
PATTERN_FIRECREST_POS = 's_%s_%s_pos.txt'
PATTERN_FIRECREST_IDX = 's_%s_%s_idx.txt'
PATTERN_FIRECREST_CLU1 = 's_%s_%s_01_1_clu.txt'
PATTERN_FIRECREST_CLU2 = 's_%s_%s_01_2_clu.txt'
PATTERN_FIRECREST_CLU3 = 's_%s_%s_01_3_clu.txt'
PATTERN_FIRECREST_CLU4 = 's_%s_%s_01_4_clu.txt'


# BUSTARD PATTERNS
# _p2f(<pattern>, lane, tile)
PATTERN_BUSTARD_SIG2 = 's_%s_%s_sig2.txt'
PATTERN_BUSTARD_PRB = 's_%s_%s_prb.txt'



# GERALD PATTERNS
# _p2f(<pattern>, lane, tile)
PATTERN_GERALD_ALLTMP = 's_%s_%s_all.txt.tmp'
PATTERN_GERALD_QRAWTMP = 's_%s_%s_qraw.txt.tmp'
PATTERN_GERALD_ALLPNGTMP = 's_%s_%s_all.tmp.png'
PATTERN_GERALD_ALIGNTMP = 's_%s_%s_align.txt.tmp'
PATTERN_GERALD_QVALTMP = 's_%s_%s_qval.txt.tmp'
PATTERN_GERALD_SCORETMP = 's_%s_%s_score.txt.tmp'
PATTERN_GERALD_PREALIGNTMP = 's_%s_%s_prealign.txt.tmp'
PATTERN_GERALD_REALIGNTMP = 's_%s_%s_realign.txt.tmp'
PATTERN_GERALD_RESCORETMP = 's_%s_%s_rescore.txt.tmp'
PATTERN_GERALD_RESCOREPNG = 's_%s_%s_rescore.png'
PATTERN_GERALD_ERRORSTMPPNG = 's_%s_%s_errors.tmp.png'
PATTERN_GERALD_QCALTMP = 's_%s_%s_qcal.txt.tmp'
PATTERN_GERALD_QVAL = 's_%s_%s_qval.txt'

# _p2f(<pattern>, lane)
PATTERN_GERALD_SEQPRETMP = 's_%s_seqpre.txt.tmp'
PATTERN_GERALD_RESULTTMP = 's_%s_eland_result.txt.tmp'
PATTERN_GERALD_SIGMEANSTMP = 's_%s_Signal_Means.txt.tmp'
PATTERN_GERALD_CALLPNG = 's_%s_call.png'
PATTERN_GERALD_ALLPNG = 's_%s_all.png'
PATTERN_GERALD_PERCENTALLPNG = 's_%s_percent_all.png'
PATTERN_GERALD_PERCENTCALLPNG = 's_%s_percent_call.png'
PATTERN_GERALD_PERCENTBASEPNG = 's_%s_percent_base.png'
PATTERN_GERALD_FILTTMP = 's_%s_filt.txt.tmp'
PATTERN_GERALD_FRAGTMP = 's_%s_frag.txt.tmp'
PATTERN_GERALD_QREPORTTMP = 's_%s_qreport.txt.tmp'
PATTERN_GERALD_QTABLETMP = 's_%s_qtable.txt.tmp'
PATTERN_GERALD_QCALREPORTTMP = 's_%s_qcalreport.txt.tmp'
PATTERN_GERALD_SEQUENCETMP = 's_%s_sequence.txt.tmp'
PATTERN_GERALD_LANEFINISHED = 's_%s_finished.txt'



def _p2f(pattern, lane, tile=None, cycle=None):
  """
  Converts a pattern plus info into file names
  """

  # lane, and cycle provided (INVALID)
  if tile is None and cycle is not None:
    msg = "Handling of cycle without tile is not currently implemented."
    raise ValueError, msg

  # lane, tile, cycle provided
  elif cycle:
    return pattern % (lane,
                      "%04d" % (tile,),
		      "%02d" % (cycle,))
  
  # lane, tile provided
  elif tile:
    return pattern % (lane, "%04d" % (tile,))

  # lane provided
  else:
    return pattern % (lane)
    

class GARunStatus(object):

  def __init__(self, conf_filepath):
    """
    Given an eland config file in the top level directory
    of a run, predicts the files that will be generated
    during a run and provides methods for retrieving
    (completed, total) for each step or entire run.
    """
    #print 'self._conf_filepath = %s' % (conf_filepath)
    self._conf_filepath = conf_filepath
    self._base_dir, junk = os.path.split(conf_filepath)
    self._image_dir = os.path.join(self._base_dir, 'Images')
    
    self.lanes = []
    self.lane_read_length = {}
    self.tiles = None
    self.cycles = None
    
    self.status = {}
    self.status['firecrest'] = {}
    self.status['bustard'] = {}
    self.status['gerald'] = {}
    
    self._process_config()
    self._count_tiles()
    self._count_cycles()
    self._generate_expected()


  def _process_config(self):
    """
    Grabs info from self._conf_filepath
    """
    f = open(self._conf_filepath, 'r')

    for line in f:

      #Skip comment lines for now.
      if s_comment.search(line):
        continue

      mo =  s_general_read_len.search(line)
      if mo:
        read_length = int(line[mo.end():])
        #Handle general READ_LENGTH
        for i in range(1,9):
          self.lane_read_length[i] = read_length
      
      mo = s_read_len.search(line)
      if mo:
        read_length = int(line[mo.end():])
        lanes, junk = line.split(':')

        #Convert lanes from string of lanes to list of lane #s.
        lanes = [ int(i) for i in lanes ]

        
        for lane in lanes:

          #Keep track of which lanes are being run.
          if lane not in self.lanes:
            self.lanes.append(lane)

          #Update with lane specific read lengths
          self.lane_read_length[lane] = read_length

        self.lanes.sort()


  def _count_tiles(self):
    """
    Count the number of tiles being used
    """
    self.tiles = len(glob.glob(os.path.join(self._image_dir,
                                            'L001',
                                            'C1.1',
                                            's_1_*_a.tif')))

  def _count_cycles(self):
    """
    Figures out the number of cycles that are available
    """
    #print 'self._image_dir = %s' % (self._image_dir)
    cycle_dirs = glob.glob(os.path.join(self._image_dir, 'L001', 'C*.1'))
    #print 'cycle_dirs = %s' % (cycle_dirs)
    cycle_list = []
    for cycle_dir in cycle_dirs:
      junk, c = os.path.split(cycle_dir)
      cycle_list.append(int(c[1:c.find('.')]))

    self.cycles = max(cycle_list)
    



  def _generate_expected(self):
    """
    generates a list of files we expect to find.
    """

    firecrest = self.status['firecrest']
    bustard = self.status['bustard']
    gerald = self.status['gerald']
    
    
    for lane in self.lanes:
      for tile in range(1,self.tiles+1):
        for cycle in range(1, self.cycles+1):

          ##########################
          # LANE, TILE, CYCLE LAYER

          # FIRECREST
          firecrest[_p2f(PATTERN_FIRECREST_QCM, lane, tile, cycle)] = False


        ###################
        # LANE, TILE LAYER

        # FIRECREST
        firecrest[_p2f(PATTERN_FIRECREST_INT, lane, tile)] = False
        firecrest[_p2f(PATTERN_FIRECREST_NSE, lane, tile)] = False
        firecrest[_p2f(PATTERN_FIRECREST_POS, lane, tile)] = False
        firecrest[_p2f(PATTERN_FIRECREST_IDX, lane, tile)] = False
        firecrest[_p2f(PATTERN_FIRECREST_CLU1, lane, tile)] = False
        firecrest[_p2f(PATTERN_FIRECREST_CLU2, lane, tile)] = False
        firecrest[_p2f(PATTERN_FIRECREST_CLU3, lane, tile)] = False
        firecrest[_p2f(PATTERN_FIRECREST_CLU4, lane, tile)] = False


        # BUSTARD
        bustard[_p2f(PATTERN_BUSTARD_SIG2, lane, tile)] = False
        bustard[_p2f(PATTERN_BUSTARD_PRB, lane, tile)] = False


        # GERALD
        #gerald[_p2f(PATTERN_GERALD_ALLTMP, lane, tile)] = False
        #gerald[_p2f(PATTERN_GERALD_QRAWTMP, lane, tile)] = False
        #gerald[_p2f(PATTERN_GERALD_ALLPNGTMP, lane, tile)] = False
        #gerald[_p2f(PATTERN_GERALD_ALIGNTMP, lane, tile)] = False
        #gerald[_p2f(PATTERN_GERALD_QVALTMP, lane, tile)] = False
        #gerald[_p2f(PATTERN_GERALD_SCORETMP, lane, tile)] = False
        #gerald[_p2f(PATTERN_GERALD_PREALIGNTMP, lane, tile)] = False
        #gerald[_p2f(PATTERN_GERALD_REALIGNTMP, lane, tile)] = False
        #gerald[_p2f(PATTERN_GERALD_RESCORETMP, lane, tile)] = False
        gerald[_p2f(PATTERN_GERALD_RESCOREPNG, lane, tile)] = False
        #gerald[_p2f(PATTERN_GERALD_ERRORSTMPPNG, lane, tile)] = False
        #gerald[_p2f(PATTERN_GERALD_QCALTMP, lane, tile)] = False
        #gerald[_p2f(PATTERN_GERALD_QVAL, lane, tile)] = False

      ###################
      # LANE LAYER

      # GERALD
      #gerald[_p2f(PATTERN_GERALD_SEQPRETMP, lane)] = False
      #gerald[_p2f(PATTERN_GERALD_RESULTTMP, lane)] = False
      #gerald[_p2f(PATTERN_GERALD_SIGMEANSTMP, lane)] = False
      gerald[_p2f(PATTERN_GERALD_CALLPNG, lane)] = False
      gerald[_p2f(PATTERN_GERALD_ALLPNG, lane)] = False
      gerald[_p2f(PATTERN_GERALD_PERCENTALLPNG, lane)] = False
      gerald[_p2f(PATTERN_GERALD_PERCENTCALLPNG, lane)] = False
      gerald[_p2f(PATTERN_GERALD_PERCENTBASEPNG, lane)] = False
      #gerald[_p2f(PATTERN_GERALD_FILTTMP, lane)] = False
      #gerald[_p2f(PATTERN_GERALD_FRAGTMP, lane)] = False
      #gerald[_p2f(PATTERN_GERALD_QREPORTTMP, lane)] = False
      #gerald[_p2f(PATTERN_GERALD_QTABLETMP, lane)] = False
      #gerald[_p2f(PATTERN_GERALD_QCALREPORTTMP, lane)] = False
      #gerald[_p2f(PATTERN_GERALD_SEQUENCETMP, lane)] = False
      gerald[_p2f(PATTERN_GERALD_LANEFINISHED, lane)] = False
      
      

    #################
    # LOOPS FINISHED

    # FIRECREST
    firecrest['offsets_finished.txt'] = False
    firecrest['finished.txt'] = False

    # BUSTARD
    bustard['finished.txt'] = False

    # GERALD
    gerald['tiles.txt'] = False
    gerald['FullAll.htm'] = False
    #gerald['All.htm.tmp'] = False
    #gerald['Signal_Means.txt.tmp'] = False
    #gerald['plotIntensity_for_IVC'] = False
    #gerald['IVC.htm.tmp'] = False
    gerald['FullError.htm'] = False
    gerald['FullPerfect.htm'] = False
    #gerald['Error.htm.tmp'] = False
    #gerald['Perfect.htm.tmp'] = False
    #gerald['Summary.htm.tmp'] = False
    #gerald['Tile.htm.tmp'] = False
    gerald['finished.txt'] = False
    
  def statusFirecrest(self):
    """
    returns (<completed>, <total>)
    """
    firecrest = self.status['firecrest']
    total = len(firecrest)
    completed = firecrest.values().count(True)

    return (completed, total)


  def statusBustard(self):
    """
    returns (<completed>, <total>)
    """
    bustard = self.status['bustard']
    total = len(bustard)
    completed = bustard.values().count(True)

    return (completed, total)


  def statusGerald(self):
    """
    returns (<completed>, <total>)
    """
    gerald = self.status['gerald']
    total = len(gerald)
    completed = gerald.values().count(True)

    return (completed, total)


  def statusTotal(self):
    """
    returns (<completed>, <total>)
    """
    #f = firecrest  c = completed
    #b = bustard    t = total
    #g = gerald
    fc, ft = self.statusFirecrest()
    bc, bt = self.statusBustard()
    gc, gt = self.statusGerald()

    return (fc+bc+gc, ft+bt+gt)


  def statusReport(self):
    """
    Generate the basic percent complete report
    """
    def _percentCompleted(completed, total):
      """
      Returns precent completed as float
      """
      return (completed / float(total)) * 100

    fc, ft = self.statusFirecrest()
    bc, bt = self.statusBustard()
    gc, gt = self.statusGerald()
    tc, tt = self.statusTotal()
    
    fp = _percentCompleted(fc, ft)
    bp = _percentCompleted(bc, bt)
    gp = _percentCompleted(gc, gt)
    tp = _percentCompleted(tc, tt)
    
    report = ['Firecrest: %s%% (%s/%s)' % (fp, fc, ft),
              '  Bustard: %s%% (%s/%s)' % (bp, bc, bt),
              '   Gerald: %s%% (%s/%s)' % (gp, gc, gt),
              '-----------------------',
              '    Total: %s%% (%s/%s)' % (tp, tc, tt),
             ]
    return report

  def updateFirecrest(self, filename):
    """
    Marks firecrest filename as being completed.
    """
    self.status['firecrest'][filename] = True
    

  def updateBustard(self, filename):
    """
    Marks bustard filename as being completed.
    """
    self.status['bustard'][filename] = True


  def updateGerald(self, filename):
    """
    Marks gerald filename as being completed.
    """
    self.status['gerald'][filename] = True



##################################################
# Functions to be called by Thread(target=<func>)
def _cmdLineStatusMonitorFunc(conf_info):
  """
  Given a ConfigInfo object, provides status to stdout.

  You should probably use startCmdLineStatusMonitor()
  instead of ths function.

  .. python:
    def example_launch():
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

    report = conf_info.status.statusReport()
    print os.linesep.join(report)
    print

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

from optparse import OptionParser
def make_parser():
  usage = "%prog: config file"

  parser = OptionParser()
  return parser
  
def main(cmdline=None):
  parser = make_parser()
  opt, args = parser.parse_args(cmdline)

  if len(args) != 1:
    parser.error("need name of configuration file")
    
  status = GARunStatus(args[0])
  print os.linesep.join(status.statusReport())
  return 0

if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
                   
