#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Author: octeau@cs.psu.edu (Damien Octeau)
# Author: theinsecureroot@gmail.com (Cyrus Vesuna)
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
"""A timed subprocess.

Do not use this on Windows. The timer relies on signal.alarm(), which is not
available on Windows.
"""

import logging
import os.path
import signal
import subprocess
import sys
WHEELBARROW_HOME = os.getenv('WHEELBARROW_HOME', os.path.dirname(__file__))
sys.path.append(WHEELBARROW_HOME)


class TimedSubprocess(object):
  """The TimedSubprocess class runs a process with a timeout.

  A timeout of 0 second means no timeout. That is the default value.
  """

  def __init__(self, timeout=0):
    self._timeout = timeout

  def Popen(self, args, bufsize=0, executable=None, stdin=None, stdout=None,
            stderr=None, preexec_fn=None, close_fds=False, shell=False,
            cwd=None, env=None, universal_newlines=False):
    """Run a command in a timed subprocess.

    If Wait() is not called and the parent terminates, then the child process
    will not be killed even if it does not terminate before the end of the
    timer. Therefore, you should call Wait() after calling Popen() unless you
    are sure that the parent will continue executing at least until the timer
    expires.

    Args:
      args: The command that should be run, as a string or list of strings.
      bufsize: 0 is unbuffered, 1 is line-buffered, n > 1 means a buffer of
               size approximately n.
      executable: Replacement program to execute.
      stdin: Standard input file handle.
      stdout: Standard output file handle.
      stderr: Standard error file handle.
      preexec_fn: Callable object which should be called in the child process
                  just before the child is executed.
      close_fds: If True, all file descriptor except 0, 1 and 2 are closed
                 before executing the child.
      shell: If True, the shell will be used as the program to execute.
      cwd: The child's current directory, if not None.
      env: Environment variables mapping for the child process.
      universal_newlines: If True, stdout and stderr are opened as text files in
                          universal newlines mode.

    Returns:
      True if the process was created successfully.
    """

    logging.info('Starting process.')
    try:
      logging.info(args)
      self._proc = subprocess.Popen(args, bufsize, executable, stdin, stdout,
                                    stderr, preexec_fn, close_fds, shell, cwd,
                                    env, universal_newlines)
    except (OSError, ValueError) as err:
      logging.error('Unable to run command %s: %s', args, err)
      return False
    signal.signal(signal.SIGALRM, self.AlarmHandler)
    # Set timer and let the process run.
    signal.alarm(self._timeout)
    return True

  def Wait(self):
    """Wait for the child process to terminate.

    The timer gets canceled if the process returns on time.

    Returns:
      The child's return code.
    """

    self._proc.wait()
    # Cancel timer.
    signal.alarm(0)
    return self._proc.returncode

  def AlarmHandler(self, unused_signalnum, unused_frame):
    """Handle a sigalrm signal by killing the process."""

    if self._proc.poll() is not None:
      # In case the parent process does not Wait() on the child and continues
      # executing.
      logging.info('Process has terminated.')
    else:
      try:
        self._proc.kill()
        logging.warning('Process was killed after timeout.')
      except OSError as err:
        logging.error('Error while trying to kill process: %s', err)
