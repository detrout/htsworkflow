"""
Run up to N simultanous jobs from provided of commands 
"""

import logging
import os
from subprocess import PIPE
import subprocess
import select
import sys
import time

class QueueCommands(object):
    """
    Queue up N commands from cmd_list, launching more jobs as the first
    finish.
    """

    def __init__(self, cmd_list, N=0, cwd=None):
        """
        cmd_list is a list of elements suitable for subprocess
        N is the  number of simultanious processes to run. 
        0 is all of them.
        
        WARNING: this will not work on windows
        (It depends on being able to pass local file descriptors to the 
        select call with isn't supported by the Win32 API)
        """
        self.to_run = cmd_list[:]
        self.running = {}
        self.N = N
        self.cwd = cwd

    def under_process_limit(self):
        """
        are we still under the total number of allowable jobs?
        """
        if self.N == 0:
            return True

        if len(self.running) < self.N:
            return True

        return False

    def start_jobs(self):
        """
        Launch jobs until we have the maximum allowable running
        (or have run out of jobs)
        """
        queue_log = logging.getLogger('queue')

        while (len(self.to_run) > 0) and self.under_process_limit():
            queue_log.info('%d left to run', len(self.to_run))
            cmd = self.to_run.pop(0)
            p = subprocess.Popen(cmd, stdout=PIPE, cwd=self.cwd, shell=True)
            self.running[p.stdout] = p
            queue_log.info("Created process %d from %s" % (p.pid, str(cmd)))

    def run(self):
        """
        run up to N jobs until we run out of jobs
        """
        queue_log = logging.getLogger('queue')
        queue_log.debug('using %s as cwd' % (self.cwd,))

        # to_run slowly gets consumed by start_jobs
        while len(self.to_run) > 0 or len(self.running) > 0:
            # fill any empty spots in our job queue
            self.start_jobs()

            # build a list of file descriptors
            # fds=file desciptors
            fds = [ x.stdout for x in self.running.values()]

            # wait for something to finish
            # wl= write list, xl=exception list (not used so get bad names)
            read_list, wl, xl = select.select(fds, [], fds, 1 )

            # for everything that might have finished...
            for pending_fd in read_list:
                pending = self.running[pending_fd]
                # if it really did finish, remove it from running jobs
                if pending.poll() is not None:
                    queue_log.info("Process %d finished [%d]",
                                   pending.pid, pending.returncode)
                    del self.running[pending_fd]
                else:
                    # It's still running, but there's some output
                    buffer = pending_fd.readline()
                    buffer = buffer.strip()
                    msg = "%d:(%d) %s" %(pending.pid, len(buffer), buffer)
                    logging.debug(msg)
            time.sleep(1)
